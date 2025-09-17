from datetime import datetime
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message, MessageEntity
from aiogram.exceptions import TelegramBadRequest

from app.keyboards.chat import CancelChatKeyboard, ClaimChatKeyboard, EndChatKeyboard
from data.config import GENERAL_CHAT_ID
from database.models import Chat, User
from database.models.messageMap import MessageMap
from loader import _
from utils import logger

router = Router()

def shift_entities(entities, shift_by: int):
    if not entities:
        return None
    shifted = []
    for e in entities:
        # Entities are immutable, need to copy
        shifted.append(
            e.copy(update={"offset": e.offset + shift_by})
        )
    return shifted

def add_bold_entity(text: str, substring: str, start_offset: int = 0):
    """Return an entity list that makes `substring` bold."""
    offset = text.find(substring, start_offset)
    if offset == -1:
        return []
    return [MessageEntity(type="bold", offset=offset, length=len(substring))]

def add_prefix(message: Message, prefix: str) -> tuple[str, list[MessageEntity]]:
    
    text = prefix + (message.text or message.caption or "")
    entities = shift_entities(message.entities or message.caption_entities or [], len(prefix))
    
    bold_entities = add_bold_entity(text, message.from_user.full_name)
    entities.extend(bold_entities)

    return text, entities

async def copy_user_message(message: Message, to_chat_id: int, reply_message_id: int = None):
    return await message.copy_to(
        chat_id=to_chat_id,
        reply_to_message_id=reply_message_id,
    )


async def new_chat(message: Message, lang: str = 'uz'):

    text = f"<a href='https://myurls.co/azcitytravel'><i>{_('A support agent will reach out to you soon.', locale=lang)}</i></a>"

    await message.reply(text=text, parse_mode="HTML")

    try:
        sent = await message.bot.send_message(chat_id=GENERAL_CHAT_ID, text=f"#kutyapti 🙋🏻‍♂️ Mijoz: <b>{message.from_user.full_name}</b> ({message.from_user.id}) \n <i>📩 1 ta o'qilmagan xabar</i>", parse_mode="HTML", reply_markup=ClaimChatKeyboard.keyboard(message.from_user.id))
        chat = await Chat.add(message.from_user.id)
        await Chat._collection.update_one({"_id": chat.id}, {"$set": {"notificated_message_id": sent.message_id, "pending_message_ids": [message.message_id]}})
    
    except ValueError:
        chat = None
        
    except Exception as e:
        chat = None
        logger.error(f"Error creating chat: {e}")

    
    return chat



# --- USER MESSAGE FORWARDING (text + media) ---
@router.message(
    F.chat.type == "private",                 # only private messages from users
    ~F.via_bot,                               # not messages from other bots
    ~F.text.startswith("/")                   # exclude commands like /start, /help
)
async def forward_user_msg(message: Message):
    user = message.from_user
    logger.info(f"Forwarding message {message.text}")

    # Find the user's active chat
    chat = await Chat._collection.find_one({
        "user_id": user.id,
        "status": {"$in": ["active", "pending"]},
    })
    

    if not chat:
        client = await User.get(user.id)
        await new_chat(message=message, lang=client.lang)
        return

    if chat['status'] == 'pending' and chat["notificated_message_id"]:
        
        await Chat._collection.update_one(
            {"_id": chat["_id"]},
             {"$push": {"pending_message_ids": message.message_id}}
        )
        
        await message.bot.edit_message_text(
            chat_id=GENERAL_CHAT_ID,
            message_id=chat["notificated_message_id"],
            text=f"#kutyapti 🙋🏻‍♂️ Mijoz: <b>{user.full_name}</b> ({user.id}) \n <i>📩 {len(chat['pending_message_ids']) + 1} ta o'qilmagan xabar</i>",
            parse_mode="HTML",
            reply_markup=ClaimChatKeyboard.keyboard(user.id)
        )

        return
    

    group_id = chat["support_group_id"]
    notice_message_id = chat.get("notice_message_id")

    group_id = chat.get("support_group_id")
    if not group_id:
        logger.error(f"Chat for user {user.id} is missing support_group_id!")
        return

    text = ""
    sent = None
    
    try:
        sent = await copy_user_message(message, group_id, notice_message_id)
    except TelegramBadRequest as e:
        logger.info("Forwading without reply")
        sent = await copy_user_message(message, group_id, None)
    except Exception as e:
        logger.error(f"Error forwarding message: {e}")
        return

    if sent:
        # Store message mapping for edit support
        await MessageMap._collection.insert_one({
            "user_id": user.id,
            "user_msg_id": message.message_id,
            "group_id": str(group_id),
            "group_msg_id": sent.message_id,
            "direction": "user_to_group",
            "created_at": int(datetime.now().timestamp())
        })


@router.callback_query(CancelChatKeyboard.Callback.filter())
async def _cancel_chat(callback: CallbackQuery, callback_data: CancelChatKeyboard.Callback):
    await callback.answer()
    await callback.message.edit_text(text=_("Chat cancelled."))
    
    try:
        chat = await Chat._collection.find_one({
                "user_id": callback.from_user.id,
                "status": "pending",
        })
        
        if chat and chat["notificated_message_id"]:
            await callback.bot.delete_message(GENERAL_CHAT_ID, chat["notificated_message_id"])
            await Chat._collection.update_many({"user_id": callback.from_user.id, "status": "pending"}, {"$set": {"status": "cancelled", "cancelled_at": int(datetime.now().timestamp())}})
    except Exception as e:
        logger.error(f"Error cancelling chat: {e}")
    
    return


@router.callback_query(EndChatKeyboard.Callback.filter())
async def _end_chat(callback: CallbackQuery, callback_data: EndChatKeyboard.Callback):
    await callback.answer()
    
    try:
        chat = await Chat._collection.find_one({
                "_id": int(callback_data.chatId),
                "status": "active",
        })

        if not chat:
            return

        user = await User._collection.find_one({
                "_id": chat['user_id'],
        })
        
        group = await callback.bot.get_chat(chat["support_group_id"])

        chatting_time = datetime.now().timestamp() - chat["created_at"]
        hours, remainder = divmod(chatting_time, 3600)
        minutes, seconds = divmod(remainder, 60)

        close_text = f"#yopildi ✈️ Suhbat yakunladi: \n Admin: <b>{callback.from_user.full_name}</b> \n Mijoz: <b>{user['name']}</b> ({user['_id']}) \n Guruh: <b>{group.title}</b> \n Suhbat vaqti: {hours} soat, {minutes} daqiqa, {round(seconds)} soniya"
        await callback.message.edit_text(text=close_text, reply_markup=None, parse_mode="HTML")

        if chat and chat["notificated_message_id"]:
            await Chat._collection.update_many({"_id": int(callback_data.chatId)}, {"$set": {"status": "ended", "finished_at": int(datetime.now().timestamp())}})
            await callback.bot.send_message(chat_id=chat["support_group_id"], text=close_text, parse_mode="HTML")
            await callback.bot.send_message(chat_id=chat["user_id"], text=f"<a href='https://myurls.co/azcitytravel'><i>{_("Talk ended", locale=user['lang'])}</i></a>")
            await callback.bot.edit_message_text(chat_id=GENERAL_CHAT_ID, message_id=chat["notificated_message_id"], text=close_text)

    except Exception as e:
        logger.error(f"Error ending chat: {e}")

    return