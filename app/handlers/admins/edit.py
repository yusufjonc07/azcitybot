from aiogram import Router, F
from aiogram.types import Message, MessageDeletionEvent
from database.models import Chat, User
from motor.motor_asyncio import AsyncIOMotorCollection
from datetime import datetime
from utils import logger

from database.models.messageMap import MessageMap

router = Router()

@router.edited_message(
    F.chat.type == "private",                 # only private messages from users
    ~F.via_bot,                               # not messages from other bots
    ~F.text.startswith("/")                   # exclude commands like /start, /help
)

async def on_user_edit(message: Message):
    
    logger.info("User edit received", message.message_id)
    
    # Find mapping for user->group
    mapping = await MessageMap._collection.find_one({
        "user_id": message.from_user.id,
        "user_msg_id": message.message_id,
        "direction": "user_to_group"
    })
    if not mapping:
        logger.info("No mapping found for user edit", message.message_id)
        return
    try:
        await message.bot.edit_message_text(
            chat_id=mapping["group_id"],
            message_id=mapping["group_msg_id"],
            text=message.text
        )
    except Exception as e:
        print(f"Failed to edit forwarded group message: {e}")



@router.edited_message()
async def on_admin_edit(message: Message):
    logger.info("Admin edit received", message.message_id)
    # Find mapping for group->user
    mapping = await MessageMap._collection.find_one({
        "group_id": message.chat.id,
        "group_msg_id": message.message_id,
        "direction": "group_to_user"
    })
    if not mapping:
        return
    try:
        await message.bot.edit_message_text(
            chat_id=mapping["user_id"],
            message_id=mapping["user_msg_id"],
            text=message.text
        )
    except Exception as e:
        print(f"Failed to edit forwarded user message: {e}")