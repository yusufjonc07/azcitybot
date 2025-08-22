from aiogram import Router
from aiogram.types import Message
from aiogram.filters import CommandObject, Command
from database.models import User
from loader import _

router = Router()

# /admin @username command handler
@router.message(Command("admin"))
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
