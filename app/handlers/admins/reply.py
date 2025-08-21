from aiogram.types import CallbackQuery, Message
from app.handlers.routers import admin_router as router
from app.keyboards.chat import ClaimChatKeyboard, EndChatKeyboard
from database.models import Chat, User
from loader import _
import re

# --- ADMIN REPLY HANDLER (text + media) ---
@router.message()
async def admin_reply(message: Message):
    print("spdfep")
    # Check if this chat is one of the admin groups
    is_admin_group = await User._collection.find_one({
    "admin_groups": {"$in": [str(message.chat.id)]}
})

    if not is_admin_group:
        return 

    if not message.reply_to_message:
        return

    # Extract user_id from the replied-to message
    match = re.search(r"\((\d+)\)", message.reply_to_message.text or message.reply_to_message.caption or "")
    if not match:
        print("no user id found")
        return

    user_id = int(match.group(1))

    try:
        sent = None
        if message.text:
            sent = await message.bot.send_message(user_id, message.text)
        elif message.photo:
            sent = await message.bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption or "")
        elif message.document:
            sent = await message.bot.send_document(user_id, message.document.file_id, caption=message.caption or "")
        elif message.video:
            sent = await message.bot.send_video(user_id, message.video.file_id, caption=message.caption or "")
        elif message.voice:
            sent = await message.bot.send_voice(user_id, message.voice.file_id, caption=message.caption or "")
        elif message.sticker:
            sent = await message.bot.send_sticker(user_id, message.sticker.file_id)
        else:
            sent = await message.bot.send_message(user_id, "[Unsupported message type]")

        if sent:
            # keep last message tracking in sync
            await Chat._collection.update_one(
                {"user_id": user_id, "status": "active"},
                {"$set": {"last_message_id": sent.message_id}}
            )

    except Exception as e:
        print(f"❌ Failed to send to user {user_id}: {e}")
