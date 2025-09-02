from datetime import datetime
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest

from app.keyboards.chat import CancelChatKeyboard, ClaimChatKeyboard, EndChatKeyboard
from data.config import GENERAL_CHAT_ID
from database.models import Chat, User
from database.models.messageMap import MessageMap
from loader import _
from utils import logger

router = Router()

async def new_chat(message: Message, lang: str = 'uz'):

    text = f"<a href='https://myurls.co/azcitytravel'><tg-emoji custom_emoji_id='5474330856958994237'>✅</tg-emoji>{_('A support agent will reach out to you soon.', locale=lang)}</a>"

    await message.reply(text=text, parse_mode="HTML")

    try:
        chat = await Chat.add(message.from_user.id)
        sent = await message.bot.send_message(
            chat_id=GENERAL_CHAT_ID,
            text=f"#kutyapti Mijoz: <b>{message.from_user.full_name}</b> ({message.from_user.id}) \n 💬 {message.text}",
            reply_markup=ClaimChatKeyboard.keyboard(message.from_user.id),
            parse_mode="HTML"
        )
        await Chat._collection.update_one({"_id": chat.id}, {"$set": {"notificated_message_id": sent.message_id}})
    except ValueError:
        chat = None
        
    except Exception as e:
        chat = None
        logger.error(f"Error creating chat: {e}")

    
    return chat


async def forward_message(message: Message, group_id: int, fmt_caption: any, last_message_id: int = None):
    
    
    
    if message.text:
        return await message.bot.send_message(
            chat_id=group_id,
            text=fmt_caption(message.text),
            reply_to_message_id=last_message_id,
            parse_mode="HTML"
        )
    elif message.photo:
        return await message.bot.send_photo(
            chat_id=group_id,
            photo=message.photo[-1].file_id,
            caption=fmt_caption(message.caption or ""),
            reply_to_message_id=last_message_id,
            parse_mode="HTML"
        )
    elif message.document:
        return await message.bot.send_document(
            chat_id=group_id,
            document=message.document.file_id,
            caption=fmt_caption(message.caption or ""),
            reply_to_message_id=last_message_id,
            parse_mode="HTML"
        )
    elif message.video:
        return await message.bot.send_video(
            chat_id=group_id,
            video=message.video.file_id,
            caption=fmt_caption(message.caption or ""),
            reply_to_message_id=last_message_id,
            parse_mode="HTML"
        )
    elif message.voice:
        return await message.bot.send_voice(
            chat_id=group_id,
            voice=message.voice.file_id,
            caption=fmt_caption(message.caption or ""),
            reply_to_message_id=last_message_id,
            parse_mode="HTML"
        )
    elif message.sticker:
        return await message.bot.send_sticker(
            chat_id=group_id,
            sticker=message.sticker.file_id,
            reply_to_message_id=last_message_id,
            parse_mode="HTML"
        )
    else:
        return await message.bot.send_message(
            chat_id=group_id,
            text=fmt_caption("[Unsupported message type]"),
            reply_to_message_id=last_message_id,
            parse_mode="HTML"
        )
    
    return None


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
        "status": "active",
        "support_group_id": {"$ne": None}
    })
    

    if not chat:
        client = await User.get(user.id)
        await new_chat(message=message, lang=client.lang)
        return

    group_id = chat["support_group_id"]
    last_message_id = chat.get("last_message_id")

    # Prepare formatted caption for all media/text
    def fmt_caption(base_text: str = ""):
        return f"💬 <b>{user.full_name}</b> ({user.id})\n\n{base_text}"


    try:
        sent = await forward_message(message, group_id, fmt_caption, last_message_id)
    except TelegramBadRequest as e:
        logger.info("Forwading without reply")
        sent = await forward_message(message, group_id, fmt_caption, None)
    except Exception as e:
        logger.error(f"Error forwarding message: {e}")
        return

    if sent:
        await Chat._collection.update_one(
            {"user_id": user.id, "status": "active"},
            {"$set": {"last_message_id": sent.message_id}}
        )
        # Store message mapping for edit support
        await MessageMap._collection.insert_one({
            "user_id": user.id,
            "user_msg_id": message.message_id,
            "group_id": group_id,
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
        user = await User._collection.find_one({
                "_id": chat['user_id'],
        })
        
        group = await callback.bot.get_chat(chat["support_group_id"])

        chatting_time = datetime.now().timestamp() - chat["created_at"]
        hours, remainder = divmod(chatting_time, 3600)
        minutes, seconds = divmod(remainder, 60)

        close_text = f"#yopildi \n Suhbat yakunladi: <b>{callback.from_user.full_name}</b> ({callback.from_user.id})"
        await callback.message.edit_text(text=f"✈️ Suhbat yakunladi: \n Admin: <b>{callback.from_user.full_name}</b> \n Mijoz: <b>{user.full_name}</b> ({user.id}) \n Guruh: <b>{group.title}</b> \n Suhbat vaqti: {hours} soat, {minutes} daqiqa, {seconds} soniya", reply_markup=None, parse_mode="HTML")

        if chat and chat["notificated_message_id"]:
            await Chat._collection.update_many({"_id": int(callback_data.chatId)}, {"$set": {"status": "ended", "finished_at": int(datetime.now().timestamp())}})
            await callback.bot.send_message(chat_id=chat["support_group_id"], text=close_text, parse_mode="HTML")
            await callback.bot.send_message(chat_id=chat["user_id"], text=_("Talk ended", locale=user['lang']))
            await callback.bot.edit_message_text(chat_id=GENERAL_CHAT_ID, message_id=chat["notificated_message_id"], text=close_text)

    except Exception as e:
        logger.error(f"Error ending chat: {e}")

    return