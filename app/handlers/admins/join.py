from aiogram import Router
from aiogram.types import Message
from database.models import User
from loader import _

router = Router()

# Automatically add new group member as admin in the bot
@router.message()
async def on_new_member(message: Message):
    if message.new_chat_members:
        for new_user in message.new_chat_members:
            user_id = new_user.id
            group_id = str(message.chat.id)

            # Fetch user from DB
            user = await User.get(user_id)
            if not user:
                # Optionally create the user here if needed
                continue

            # Ensure admin_groups exists
            if not hasattr(user, "admin_groups") or user.admin_groups is None:
                user.admin_groups = []

            # Add group_id if not already present
            if group_id not in user.admin_groups:
                user.admin_groups.append(group_id)
                await User._collection.update_one(
                    {"_id": user_id},
                    {"$set": {"admin_groups": user.admin_groups}}
                )
                await message.reply(
                    _(f"{new_user.full_name} is now an admin for this group!")
                )
