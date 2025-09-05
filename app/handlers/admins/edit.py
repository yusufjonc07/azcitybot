from aiogram import Router, F
from aiogram.types import Message, MessageReactionUpdated, ReactionTypeEmoji
from database.models import Chat, User
from motor.motor_asyncio import AsyncIOMotorCollection
from datetime import datetime
from utils import logger
from loader import _

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
    
    user = message.from_user
    try:
        # Format the message with edit timestamp
        edit_datetime = datetime.fromtimestamp(message.edit_date)
        edit_time = edit_datetime.strftime("%H:%M")
        edited_text = f"💬 <b>{user.full_name}</b> ({user.id})\n\n{message.text}\n\n<i>✎ {_("edited", locale='uz')} • {edit_time}</i>"
        await message.bot.edit_message_text(
            chat_id=mapping["group_id"],
            message_id=mapping["group_msg_id"],
            text=edited_text,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Failed to edit forwarded group message: {e}")



@router.edited_message()
async def on_admin_edit(message: Message):
    logger.info("Admin edit received", message.message_id)
    # Find mapping for group->user
    mapping = await MessageMap._collection.find_one({
        "group_id": str(message.chat.id),
        "group_msg_id": message.message_id,
        "direction": "group_to_user"
    })
    if not mapping:
        return
    user = await User.get(mapping['user_id'])
    
    if not user:
        return

    # Format the message with edit timestamp
    edit_datetime = datetime.fromtimestamp(message.edit_date)
    edit_time = edit_datetime.strftime("%H:%M")
    edited_text = f"{message.text}\n\n<i>✎ {_("edited", locale=user.lang)} • {edit_time}</i>"

    try:
        await message.bot.edit_message_text(
            chat_id=mapping["user_id"],
            message_id=mapping["user_msg_id"],
            text=edited_text,
            parse_mode="HTML"
        )
    except Exception as e:
        print(f"Failed to edit forwarded user message: {e}")

# --- USER REACTION HANDLER ---
@router.message_reaction(F.chat.type == "private")
async def on_user_reaction(event: MessageReactionUpdated):
    
    print("User Reaction", event.chat.id, event.message_id)
    # Find mapping for the message that was reacted to
    mapping = await MessageMap._collection.find_one({
        "user_id": event.chat.id,
        "user_msg_id": event.message_id,
        "direction": "user_to_group"
    })
    # If no mapping found, try the reverse direction
    if not mapping:
        mapping = await MessageMap._collection.find_one({
            "user_id": event.chat.id,
            "user_msg_id": event.message_id,
            "direction": "group_to_user"
        })
    
    
    if not mapping:
        logger.info(f"No mapping found for user reaction: ")
        return
    
    try:
        # Set reactions on the admin group message
        sent = await event.bot.set_message_reaction(
            chat_id=mapping["group_id"],
            message_id=mapping["group_msg_id"],
            reaction=event.new_reaction
        )

        logger.info(f"Reaction sent: {sent}")

    except Exception as e:
        logger.error(f"Failed to sync user reaction to group: {e}")

# --- ADMIN REACTION HANDLER ---
@router.message_reaction(F.chat.type == "group")
async def on_admin_reaction(event: MessageReactionUpdated):

    print("Admin Reaction", event.chat.id, event.message_id)
    
    # Find mapping for the message that was reacted to
    mapping = await MessageMap._collection.find_one({
        "group_id": str(event.chat.id),
        "group_msg_id": event.message_id,
        "direction": "user_to_group"
    })
    # If no mapping found, try the reverse direction
    if not mapping:
        mapping = await MessageMap._collection.find_one({
            "group_id": str(event.chat.id),
            "group_msg_id": event.message_id,
            "direction": "group_to_user"
        })
    if not mapping:
        logger.info(f"No mapping found for admin reaction: ")
        return
    
    try:
        # Set reactions on the user message
        sent = await event.bot.set_message_reaction(
            chat_id=mapping["user_id"],
            message_id=mapping["user_msg_id"],
            reaction=event.new_reaction
        )
        
        logger.info(f"Reaction sent: {sent}")
    except Exception as e:
        logger.error(f"Failed to sync admin reaction to user: {e}")