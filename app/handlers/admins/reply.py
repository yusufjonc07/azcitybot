from aiogram import Router, F
from aiogram.types import Message
from database.models import Chat, User
from loader import _
from aiogram.filters import Filter, Command
from aiogram.types import Message

import re
from utils import logger

router = Router()

class IsReply(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.reply_to_message != None



# /admin @username command handler
@router.message()
async def add_admin_command(message: Message):
    print("Received /admin command")
    if not message.chat or message.chat.type not in ("group", "supergroup"):
        await message.reply(_("This command can only be used in groups."))
        return
    # Parse username from message.text
    parts = message.text.strip().split()
    if len(parts) < 2 or not parts[1].startswith("@"):
        await message.reply(_("Usage: /admin @username"))
        return
    username = parts[1].lstrip("@")
    user = await User._collection.find_one({"username": username})
    if not user:
        await message.reply(_(f"User @{username} not found in the bot database."))
        return
    group_id = str(message.chat.id)
    admin_groups = user.get("admin_groups", [])
    if group_id not in admin_groups:
        admin_groups.append(group_id)
        await User._collection.update_one({"_id": user["_id"]}, {"$set": {"admin_groups": admin_groups}})
        await message.reply(_(f"@{username} is now an admin for this group!"))
    else:
        await message.reply(_(f"@{username} is already an admin for this group."))



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
        if message.text:
            await message.bot.send_message(user_id, message.text)
        elif message.photo:
            await message.bot.send_photo(user_id, message.photo[-1].file_id, caption=message.caption or "")
        elif message.document:
            await message.bot.send_document(user_id, message.document.file_id, caption=message.caption or "")
        elif message.video:
            await message.bot.send_video(user_id, message.video.file_id, caption=message.caption or "")
        elif message.voice:
            await message.bot.send_voice(user_id, message.voice.file_id, caption=message.caption or "")
        elif message.sticker:
            await message.bot.send_sticker(user_id, message.sticker.file_id)
        else:
            await message.bot.send_message(user_id, "[Unsupported message type]")

        # keep last message tracking in sync
        await Chat._collection.update_one(
            {"user_id": user_id, "status": "active"},
            {"$set": {"last_message_id": message.message_id}}
        )

    except Exception as e:
        logger.error(f"Failed to send to user {user_id}: {e}")
