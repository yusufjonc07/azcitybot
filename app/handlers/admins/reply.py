from aiogram import Router, F
from aiogram.types import Message
from database.models import Chat, User
from database.models.messageMap import MessageMap
from loader import _
from aiogram.filters import Filter, Command
from aiogram.types import Message, ChatMemberUpdated

import re
from utils import logger

router = Router()

class IsReply(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.reply_to_message != None


# --- ADMIN REPLY HANDLER (text + media) ---
@router.message(IsReply(), ~F.text.startswith("/")         )
async def admin_reply(message: Message):
    logger.info("Admin reply received", message.message_id)
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
        logger.error("No user id found")
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

        # keep last message tracking in sync
        await Chat._collection.update_one(
            {"user_id": user_id, "status": "active"},
            {"$set": {"last_message_id": message.message_id}}
        )

        # Store message mapping for edit support (admin->user)
        if sent:
            await MessageMap._collection.insert_one({
                "user_id": user_id,
                "user_msg_id": sent.message_id,
                "group_id": str(message.chat.id),
                "group_msg_id": message.message_id,
                "direction": "group_to_user",
                "created_at": int(message.date.timestamp())
            })

    except Exception as e:
        logger.error(f"Failed to send to user {user_id}: {e}")
