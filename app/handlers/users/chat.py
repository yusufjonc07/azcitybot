from datetime import datetime
from aiogram.filters import Command
from aiogram import F
from aiogram.types import CallbackQuery, Message

from app.keyboards import LangKeyboard
from app.handlers.routers import user_router as router
from app.keyboards.chat import CancelChatKeyboard, ClaimChatKeyboard, NewChatKeyboard, EndChatKeyboard
from data.config import GENERAL_CHAT_ID
from database.models import Chat, User
from loader import _

@router.callback_query(NewChatKeyboard.Callback.filter())
async def _new_chat(callback: CallbackQuery, callback_data: NewChatKeyboard.Callback):
    await callback.answer("Processing your request...", show_alert=False)
    user = await User.get(callback.from_user.id)
    try:
        chat = await Chat.add(callback.from_user.id)
        print("Chat created:", chat)
        sent = await callback.bot.send_message(
            chat_id=GENERAL_CHAT_ID,
            text=f"#kutyapti Mijoz: {callback.from_user.full_name} ({callback.from_user.id})",
            reply_markup=ClaimChatKeyboard.keyboard(callback.from_user.id)
        )
        await Chat._collection.update_one({"_id": chat.id}, {"$set": {"notificated_message_id": sent.message_id}})
    except ValueError:
        chat = None
        
    except Exception as e:
        chat = None
        print(f"Error creating chat: {e}")

    await callback.message.edit_text(text=_("A support agent will reach out to you soon.", locale=user.lang))
    return 
# --- USER MESSAGE FORWARDING (text + media) ---
@router.message(
    F.chat.type == "private",                 # only private messages from users
    ~F.via_bot,                               # not messages from other bots
    ~F.text.startswith("/")                   # exclude commands like /start, /help
)
async def forward_user_msg(message: Message):
    user = message.from_user
    print(f"Forwarding message {message.text}")

    # Find the user's active chat
    chat = await Chat._collection.find_one({
        "user_id": user.id,
        "status": "active",
        "support_group_id": {"$ne": None}
    })

    if not chat:
        print(f"No active")
        # no active chat = ignore silently (or handle pending/unclaimed separately)
        return

    group_id = chat["support_group_id"]
    last_message_id = chat.get("last_message_id")

    # Prepare formatted caption for all media/text
    def fmt_caption(base_text: str = ""):
        return f"💬 {user.full_name} ({user.id})\n\n{base_text}"

    sent = None

    if message.text:
        sent = await message.bot.send_message(
            chat_id=group_id,
            text=fmt_caption(message.text),
            reply_to_message_id=last_message_id
        )
    elif message.photo:
        sent = await message.bot.send_photo(
            chat_id=group_id,
            photo=message.photo[-1].file_id,
            caption=fmt_caption(message.caption or ""),
            reply_to_message_id=last_message_id
        )
    elif message.document:
        sent = await message.bot.send_document(
            chat_id=group_id,
            document=message.document.file_id,
            caption=fmt_caption(message.caption or ""),
            reply_to_message_id=last_message_id
        )
    elif message.video:
        sent = await message.bot.send_video(
            chat_id=group_id,
            video=message.video.file_id,
            caption=fmt_caption(message.caption or ""),
            reply_to_message_id=last_message_id
        )
    elif message.voice:
        sent = await message.bot.send_voice(
            chat_id=group_id,
            voice=message.voice.file_id,
            caption=fmt_caption(message.caption or ""),
            reply_to_message_id=last_message_id
        )
    elif message.sticker:
        sent = await message.bot.send_sticker(
            chat_id=group_id,
            sticker=message.sticker.file_id,
            reply_to_message_id=last_message_id
        )
    else:
        sent = await message.bot.send_message(
            chat_id=group_id,
            text=fmt_caption("[Unsupported message type]"),
            reply_to_message_id=last_message_id
        )

    if sent:
        await Chat._collection.update_one(
            {"_id": chat["_id"]},
            {"$set": {"last_message_id": sent.message_id}}
        )


# @router.callback_query(CancelChatKeyboard.Callback.filter())
# async def _cancel_chat(callback: CallbackQuery, callback_data: CancelChatKeyboard.Callback):
#     await callback.answer()
#     chat = await Chat._collection.find_one({
#             "user_id": callback.from_user.id,
#             "status": "pending",
#     })
    
#     if chat and chat["notificated_message_id"]:
#         await callback.bot.delete_message(GENERAL_CHAT_ID, chat["notificated_message_id"])
#         await Chat._collection.update_many({"user_id": callback.from_user.id, "status": "pending"}, {"$set": {"status": "cancelled", "cancelled_at": int(datetime.now().timestamp())}})

#     await callback.message.edit_text(text=_("Chat cancelled."), reply_markup=NewChatKeyboard.keyboard())
#     return