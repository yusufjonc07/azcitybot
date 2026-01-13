"""
Edit and reaction handlers for support chats.
Uses PostgreSQL for database operations.
"""
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, MessageReactionUpdated
from sqlmodel import select

from app.bot_client.loader import _
from app.bot_client.database import get_session
from app.bot_client.services.user_service import UserService
from app.models import SupportChat, MessageMap, ChatStatus
import logging

logger = logging.getLogger(__name__)

router = Router()


@router.edited_message(
    F.chat.type == "private",
    ~F.via_bot,
    ~F.text.startswith("/")
)
async def on_user_edit(message: Message):
    """Handle edited messages from users."""
    logger.info(f"User edit received: {message.message_id}")

    with get_session() as session:
        # Find mapping for user->group
        user = UserService.get_by_telegram_id(session, message.from_user.id)
        if not user:
            return

        statement = select(MessageMap, SupportChat).join(
            SupportChat, MessageMap.chat_id == SupportChat.id
        ).where(
            SupportChat.user_id == user.id,
            MessageMap.user_message_id == message.message_id
        )
        result = session.exec(statement).first()

        if not result:
            logger.info(f"No mapping found for user edit: {message.message_id}")
            return

        mapping, chat = result

        try:
            # Format the message with edit timestamp
            edit_datetime = datetime.fromtimestamp(message.edit_date)
            edit_time = edit_datetime.strftime("%H:%M")
            edited = _("edited", locale="uz")
            edited_text = f"💬 <b>{message.from_user.full_name}</b> ({message.from_user.id})\n\n{message.text}\n\n<i>✎ {edited} • {edit_time}</i>"
            
            await message.bot.edit_message_text(
                chat_id=chat.support_group_id,
                message_id=mapping.support_message_id,
                text=edited_text,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to edit forwarded group message: {e}")


@router.edited_message(F.chat.type.in_({"group", "supergroup"}))
async def on_admin_edit(message: Message):
    """Handle edited messages from admins in support groups."""
    logger.info(f"Admin edit received: {message.message_id}")

    with get_session() as session:
        # Find mapping for group->user
        statement = select(MessageMap, SupportChat).join(
            SupportChat, MessageMap.chat_id == SupportChat.id
        ).where(
            SupportChat.support_group_id == message.chat.id,
            MessageMap.support_message_id == message.message_id
        )
        result = session.exec(statement).first()

        if not result:
            return

        mapping, chat = result
        user = chat.user

        if not user:
            return

        try:
            # Format the message with edit timestamp
            edit_datetime = datetime.fromtimestamp(message.edit_date)
            edit_time = edit_datetime.strftime("%H:%M")
            edited = _("edited", locale=user.lang)
            edited_text = f"{message.text}\n\n<i>✎ {edited} • {edit_time}</i>"

            await message.bot.edit_message_text(
                chat_id=user.telegram_id,
                message_id=mapping.user_message_id,
                text=edited_text,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to edit forwarded user message: {e}")


# --- USER REACTION HANDLER ---
@router.message_reaction(F.chat.type == "private")
async def on_user_reaction(event: MessageReactionUpdated):
    """Handle reactions from users."""
    logger.info(f"User Reaction: {event.chat.id}, {event.message_id}")

    with get_session() as session:
        user = UserService.get_by_telegram_id(session, event.chat.id)
        if not user:
            return

        # Find mapping for the message that was reacted to
        statement = select(MessageMap, SupportChat).join(
            SupportChat, MessageMap.chat_id == SupportChat.id
        ).where(
            SupportChat.user_id == user.id,
            MessageMap.user_message_id == event.message_id
        )
        result = session.exec(statement).first()

        if not result:
            logger.info(f"No mapping found for user reaction")
            return

        mapping, chat = result

        try:
            # Set reactions on the admin group message
            await event.bot.set_message_reaction(
                chat_id=chat.support_group_id,
                message_id=mapping.support_message_id,
                reaction=event.new_reaction
            )
            logger.info(f"Reaction synced to group")
        except Exception as e:
            logger.error(f"Failed to sync user reaction to group: {e}")


# --- ADMIN REACTION HANDLER ---
@router.message_reaction(F.chat.type.in_({"group", "supergroup"}))
async def on_admin_reaction(event: MessageReactionUpdated):
    """Handle reactions from admins."""
    logger.info(f"Admin Reaction: {event.chat.id}, {event.message_id}")

    with get_session() as session:
        # Find mapping for the message that was reacted to
        statement = select(MessageMap, SupportChat).join(
            SupportChat, MessageMap.chat_id == SupportChat.id
        ).where(
            SupportChat.support_group_id == event.chat.id,
            MessageMap.support_message_id == event.message_id
        )
        result = session.exec(statement).first()

        if not result:
            logger.info(f"No mapping found for admin reaction")
            return

        mapping, chat = result
        user = chat.user

        if not user:
            return

        try:
            # Set reactions on the user message
            await event.bot.set_message_reaction(
                chat_id=user.telegram_id,
                message_id=mapping.user_message_id,
                reaction=event.new_reaction
            )
            logger.info(f"Reaction synced to user")
        except Exception as e:
            logger.error(f"Failed to sync admin reaction to user: {e}")
