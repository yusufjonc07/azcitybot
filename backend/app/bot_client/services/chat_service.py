"""
Chat service for bot support operations with PostgreSQL.
"""
from datetime import datetime
from uuid import UUID

from sqlmodel import Session, select, col

from app.models import SupportChat, SupportChatCreate, SupportChatUpdate, User, ChatStatus
from .user_service import UserService


class ChatService:
    """Service for support chat database operations."""

    @staticmethod
    def get_by_id(session: Session, chat_id: UUID) -> SupportChat | None:
        """Get chat by ID."""
        return session.get(SupportChat, chat_id)

    @staticmethod
    def get_active_chat_for_user(session: Session, telegram_id: int) -> SupportChat | None:
        """Get active or pending chat for a user by Telegram ID."""
        user = UserService.get_by_telegram_id(session, telegram_id)
        if not user:
            return None
        
        statement = select(SupportChat).where(
            SupportChat.user_id == user.id,
            col(SupportChat.status).in_([ChatStatus.active, ChatStatus.pending])
        )
        return session.exec(statement).first()

    @staticmethod
    def get_pending_chat(session: Session, telegram_id: int) -> SupportChat | None:
        """Get pending chat for a user."""
        user = UserService.get_by_telegram_id(session, telegram_id)
        if not user:
            return None
        
        statement = select(SupportChat).where(
            SupportChat.user_id == user.id,
            SupportChat.status == ChatStatus.pending
        )
        return session.exec(statement).first()

    @staticmethod
    def create(session: Session, user_id: UUID, notified_message_id: int | None = None) -> SupportChat:
        """Create a new support chat."""
        chat = SupportChat(
            user_id=user_id,
            notified_message_id=notified_message_id,
            status=ChatStatus.pending,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow(),
        )
        session.add(chat)
        session.commit()
        session.refresh(chat)
        return chat

    @staticmethod
    def update(session: Session, chat: SupportChat, chat_in: SupportChatUpdate) -> SupportChat:
        """Update a support chat."""
        chat_data = chat_in.model_dump(exclude_unset=True)
        chat_data["updated_at"] = datetime.utcnow()
        chat.sqlmodel_update(chat_data)
        session.add(chat)
        session.commit()
        session.refresh(chat)
        return chat

    @staticmethod
    def add_pending_message(session: Session, chat: SupportChat, message_id: int) -> SupportChat:
        """Add a message ID to pending messages list."""
        pending = list(chat.pending_message_ids or [])
        pending.append(message_id)
        return ChatService.update(session, chat, SupportChatUpdate(pending_message_ids=pending))

    @staticmethod
    def claim_chat(session: Session, chat: SupportChat, admin_id: UUID, support_group_id: int) -> SupportChat:
        """Admin claims a chat."""
        return ChatService.update(
            session, chat,
            SupportChatUpdate(
                status=ChatStatus.active,
                admin_id=admin_id,
                support_group_id=support_group_id,
            )
        )

    @staticmethod
    def finish_chat(session: Session, chat: SupportChat) -> SupportChat:
        """Mark chat as finished."""
        return ChatService.update(session, chat, SupportChatUpdate(status=ChatStatus.finished))

    @staticmethod
    def cancel_chat(session: Session, chat: SupportChat) -> SupportChat:
        """Mark chat as cancelled."""
        return ChatService.update(session, chat, SupportChatUpdate(status=ChatStatus.cancelled))

    @staticmethod
    def update_notified_message(session: Session, chat: SupportChat, message_id: int) -> SupportChat:
        """Update the notified message ID."""
        return ChatService.update(session, chat, SupportChatUpdate(notified_message_id=message_id))

    @staticmethod
    def update_notice_message(session: Session, chat: SupportChat, message_id: int) -> SupportChat:
        """Update the notice message ID in support group."""
        return ChatService.update(session, chat, SupportChatUpdate(notice_message_id=message_id))

    @staticmethod
    def has_newer_pending_chats(session: Session, chat: SupportChat) -> bool:
        """Check if there are chats newer than this one."""
        statement = select(SupportChat).where(
            SupportChat.updated_at > chat.updated_at,
            SupportChat.status == ChatStatus.pending
        )
        result = session.exec(statement).first()
        return result is not None
