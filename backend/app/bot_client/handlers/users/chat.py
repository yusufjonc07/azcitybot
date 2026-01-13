"""
User chat handler for support conversations.
Uses PostgreSQL for database operations.
"""
from datetime import datetime
from aiogram import F, Router
from aiogram.types import CallbackQuery, Message, MessageEntity
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError

from app.bot_client.keyboards.chat import CancelChatKeyboard, ClaimChatKeyboard, EndChatKeyboard
from app.bot_client.loader import _, bot
from app.bot_client.database import get_session
from app.bot_client.services.user_service import UserService
from app.bot_client.services.chat_service import ChatService
from app.core.config import settings
from app.models import ChatStatus, SupportChatUpdate, MessageMap, MessageMapCreate
from sqlmodel import select
import logging

logger = logging.getLogger(__name__)

router = Router()


def shift_entities(entities, shift_by: int):
    """Shift entity offsets by a given amount."""
    if not entities:
        return []
    shifted = []
    for e in entities:
        shifted.append(e.model_copy(update={"offset": e.offset + shift_by}))
    return shifted


def add_bold_entity(text: str, substring: str, start_offset: int = 0):
    """Return an entity list that makes `substring` bold."""
    offset = text.find(substring, start_offset)
    if offset == -1:
        return []
    return [MessageEntity(type="bold", offset=offset, length=len(substring))]


def add_prefix(message: Message, prefix: str) -> tuple[str, list[MessageEntity]]:
    """Add prefix to message text and shift entities."""
    text = prefix + (message.text or message.caption or "")
    entities = shift_entities(message.entities or message.caption_entities or [], len(prefix))
    bold_entities = add_bold_entity(text, message.from_user.full_name)
    entities.extend(bold_entities)
    return text, entities


async def copy_user_message(message: Message, to_chat_id: int, reply_message_id: int = None):
    """Copy user message to support group."""
    return await message.copy_to(
        chat_id=to_chat_id,
        reply_to_message_id=reply_message_id,
    )


async def new_chat(message: Message, lang: str = 'uz'):
    """Create a new support chat."""
    text = f"<a href='https://myurls.co/azcitytravel'><i>{_('A support agent will reach out to you soon.', locale=lang)}</i></a>"
    await message.reply(text=text, parse_mode="HTML")

    try:
        with get_session() as session:
            # Get or create user
            user = UserService.get_or_create(
                session,
                telegram_id=message.from_user.id,
                full_name=message.from_user.full_name,
                username=message.from_user.username,
                lang=lang,
            )
            
            # Send notification to support group
            sent = await message.bot.send_message(
                chat_id=settings.SUPPORT_GROUP_ID,
                text=f"#kutyapti 🙋🏻‍♂️ Mijoz: <b>{message.from_user.full_name}</b> ({message.from_user.id}) \n @{message.from_user.username} \n <i>📩 1 ta o'qilmagan xabar</i>",
                parse_mode="HTML",
                reply_markup=ClaimChatKeyboard.keyboard(message.from_user.id)
            )
            
            # Create support chat
            chat = ChatService.create(session, user.id, sent.message_id)
            ChatService.add_pending_message(session, chat, message.message_id)
            
            return chat
            
    except Exception as e:
        logger.error(f"Error creating chat: {e}")
        return None


async def update_pending_notification(message: Message, chat, user_telegram_id: int, user_full_name: str, user_username: str | None, pending_count: int):
    """Update the pending notification in support group."""
    try:
        await message.bot.edit_message_text(
            chat_id=settings.SUPPORT_GROUP_ID,
            message_id=chat.notified_message_id,
            text=f"#kutyapti 🙋🏻‍♂️ Mijoz: <b>{user_full_name}</b> ({user_telegram_id}) \n @{user_username} \n <i>📩 {pending_count} ta o'qilmagan xabar</i>",
            parse_mode="HTML",
            reply_markup=ClaimChatKeyboard.keyboard(user_telegram_id)
        )
    except Exception:
        return
    
    # Check if there are newer chats and resend notification to bottom
    with get_session() as session:
        from app.models import SupportChat
        statement = select(SupportChat).where(
            SupportChat.updated_at > chat.updated_at,
            SupportChat.status == ChatStatus.pending
        )
        newer_chats = session.exec(statement).first()
        
        if newer_chats:
            try:
                resent_msg = await message.bot.copy_message(
                    chat_id=settings.SUPPORT_GROUP_ID,
                    from_chat_id=settings.SUPPORT_GROUP_ID,
                    message_id=chat.notified_message_id,
                    reply_markup=ClaimChatKeyboard.keyboard(user_telegram_id)
                )
                
                await message.bot.delete_message(
                    chat_id=settings.SUPPORT_GROUP_ID,
                    message_id=chat.notified_message_id
                )
                
                ChatService.update(session, chat, SupportChatUpdate(notified_message_id=resent_msg.message_id))
            except Exception as e:
                logger.error(f"Error resending notification: {e}")


# --- USER MESSAGE FORWARDING (text + media) ---
@router.message(
    F.chat.type == "private",
    ~F.via_bot,
    ~F.text.startswith("/")
)
async def forward_user_msg(message: Message):
    """Forward user messages to support group."""
    user = message.from_user
    logger.info(f"Forwarding message from {user.id}")

    with get_session() as session:
        # Get or create user
        db_user = UserService.get_or_create(
            session,
            telegram_id=user.id,
            full_name=user.full_name,
            username=user.username,
        )
        
        # Find active or pending chat
        chat = ChatService.get_active_chat_for_user(session, user.id)
        
        if not chat:
            # Create new chat
            await new_chat(message=message, lang=db_user.lang)
            return

        if chat.status == ChatStatus.pending and chat.notified_message_id:
            # Update pending notification
            pending_count = len(chat.pending_message_ids or []) + 1
            await update_pending_notification(
                message, chat, user.id, user.full_name, user.username, pending_count
            )
            ChatService.add_pending_message(session, chat, message.message_id)
            return

        # Active chat - forward to support group
        group_id = chat.support_group_id
        notice_message_id = chat.notice_message_id

        if not group_id:
            logger.error(f"Chat for user {user.id} is missing support_group_id!")
            return

        sent = None
        
        try:
            sent = await copy_user_message(message, group_id, notice_message_id)
        except TelegramBadRequest:
            logger.info("Forwarding without reply")
            sent = await copy_user_message(message, group_id, None)
        except TelegramForbiddenError:
            # Bot was kicked from group, reset chat to pending
            ChatService.update(
                session, chat,
                SupportChatUpdate(
                    support_group_id=None,
                    notice_message_id=None,
                    status=ChatStatus.pending
                )
            )
            await update_pending_notification(
                message, chat, user.id, user.full_name, user.username,
                len(chat.pending_message_ids or []) + 1
            )
            return
        except Exception as e:
            logger.error(f"Error forwarding message: {e}")
            return

        if sent:
            # Store message mapping
            msg_map = MessageMap(
                chat_id=chat.id,
                user_message_id=message.message_id,
                support_message_id=sent.message_id,
            )
            session.add(msg_map)
            session.commit()


@router.callback_query(CancelChatKeyboard.Callback.filter())
async def _cancel_chat(callback: CallbackQuery, callback_data: CancelChatKeyboard.Callback):
    """Cancel pending chat."""
    await callback.answer()
    await callback.message.edit_text(text=_("Chat cancelled."))
    
    try:
        with get_session() as session:
            chat = ChatService.get_pending_chat(session, callback.from_user.id)
            
            if chat and chat.notified_message_id:
                await callback.bot.delete_message(settings.SUPPORT_GROUP_ID, chat.notified_message_id)
                ChatService.cancel_chat(session, chat)
    except Exception as e:
        logger.error(f"Error cancelling chat: {e}")


@router.callback_query(EndChatKeyboard.Callback.filter())
async def _end_chat(callback: CallbackQuery, callback_data: EndChatKeyboard.Callback):
    """End active chat."""
    await callback.answer()
    
    try:
        with get_session() as session:
            from uuid import UUID
            from app.models import SupportChat
            
            chat = session.get(SupportChat, UUID(callback_data.chatId))
            
            if not chat or chat.status != ChatStatus.active:
                return

            user = chat.user
            if not user:
                return
            
            group = await callback.bot.get_chat(chat.support_group_id)

            chatting_time = (datetime.utcnow() - chat.created_at).total_seconds()
            hours, remainder = divmod(chatting_time, 3600)
            minutes, seconds = divmod(remainder, 60)

            close_text = f"#yopildi ✈️ Suhbat yakunladi: \n Admin: <b>{callback.from_user.full_name}</b> \n Mijoz: <b>{user.full_name}</b> ({user.telegram_id}) \n Guruh: <b>{group.title}</b> \n Suhbat vaqti: {int(hours)} soat, {int(minutes)} daqiqa, {round(seconds)} soniya"
            
            await callback.message.edit_text(text=close_text, reply_markup=None, parse_mode="HTML")
            
            if chat.notified_message_id:
                talk_ended = _("Talk ended", locale=user.lang)
                ChatService.finish_chat(session, chat)
                
                await callback.bot.send_message(chat_id=chat.support_group_id, text=close_text, parse_mode="HTML")
                await callback.bot.send_message(chat_id=user.telegram_id, text=f"<a href='https://myurls.co/azcitytravel'><i>{talk_ended}</i></a>")
                await callback.bot.edit_message_text(chat_id=settings.SUPPORT_GROUP_ID, message_id=chat.notified_message_id, text=close_text)

    except Exception as e:
        logger.error(f"Error ending chat: {e}")
