import uuid
from typing import Any

from sqlmodel import Session, select

from app.models import (
    User, UserCreate, UserUpdate,
    SupportChat, SupportChatCreate, SupportChatUpdate, ChatStatus,
    MessageMap, MessageMapCreate
)


def create_user(*, session: Session, user_create: UserCreate) -> User:
    db_obj = User.model_validate(user_create)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def update_user(*, session: Session, db_user: User, user_in: UserUpdate) -> Any:
    user_data = user_in.model_dump(exclude_unset=True)
    db_user.sqlmodel_update(user_data)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user


def get_user_by_telegram_id(*, session: Session, telegram_id: int) -> User | None:
    statement = select(User).where(User.telegram_id == telegram_id)
    session_user = session.exec(statement).first()
    return session_user


def get_or_create_user_from_telegram(
    *, 
    session: Session, 
    telegram_id: int,
    username: str | None = None,
    full_name: str | None = None,
    photo_url: str | None = None,
    lang: str = "uz",
) -> User:
    """Get existing user or create new one from Telegram login data."""
    user = get_user_by_telegram_id(session=session, telegram_id=telegram_id)
    
    if user:
        # Update user info if changed
        if username != user.username or full_name != user.full_name or photo_url != user.photo_url:
            user.username = username
            user.full_name = full_name
            user.photo_url = photo_url
            session.add(user)
            session.commit()
            session.refresh(user)
        return user
    
    # Create new user
    user_create = UserCreate(
        telegram_id=telegram_id,
        username=username,
        full_name=full_name,
        photo_url=photo_url,
        lang=lang,
    )
    return create_user(session=session, user_create=user_create)


# =============================================================================
# Support Chat CRUD Operations
# =============================================================================

def create_support_chat(*, session: Session, chat_create: SupportChatCreate) -> SupportChat:
    db_obj = SupportChat.model_validate(chat_create)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_support_chat(*, session: Session, chat_id: uuid.UUID) -> SupportChat | None:
    return session.get(SupportChat, chat_id)


def get_pending_chat_by_user(*, session: Session, user_id: uuid.UUID) -> SupportChat | None:
    statement = select(SupportChat).where(
        SupportChat.user_id == user_id,
        SupportChat.status == ChatStatus.pending
    )
    return session.exec(statement).first()


def get_active_chat_by_user(*, session: Session, user_id: uuid.UUID) -> SupportChat | None:
    statement = select(SupportChat).where(
        SupportChat.user_id == user_id,
        SupportChat.status == ChatStatus.active
    )
    return session.exec(statement).first()


def get_active_or_pending_chat_by_user(*, session: Session, user_id: uuid.UUID) -> SupportChat | None:
    statement = select(SupportChat).where(
        SupportChat.user_id == user_id,
        SupportChat.status.in_([ChatStatus.pending, ChatStatus.active])
    )
    return session.exec(statement).first()


def update_support_chat(*, session: Session, db_chat: SupportChat, chat_in: SupportChatUpdate) -> SupportChat:
    chat_data = chat_in.model_dump(exclude_unset=True)
    db_chat.sqlmodel_update(chat_data)
    session.add(db_chat)
    session.commit()
    session.refresh(db_chat)
    return db_chat


def claim_support_chat(*, session: Session, chat_id: uuid.UUID, admin_id: uuid.UUID) -> SupportChat | None:
    from datetime import datetime
    chat = get_support_chat(session=session, chat_id=chat_id)
    if chat and chat.status == ChatStatus.pending:
        chat.admin_id = admin_id
        chat.status = ChatStatus.active
        chat.claimed_at = datetime.utcnow()
        session.add(chat)
        session.commit()
        session.refresh(chat)
        return chat
    return None


def close_support_chat(*, session: Session, chat_id: uuid.UUID, cancelled: bool = False) -> SupportChat | None:
    from datetime import datetime
    chat = get_support_chat(session=session, chat_id=chat_id)
    if chat:
        if cancelled:
            chat.status = ChatStatus.cancelled
            chat.cancelled_at = datetime.utcnow()
        else:
            chat.status = ChatStatus.finished
            chat.finished_at = datetime.utcnow()
        session.add(chat)
        session.commit()
        session.refresh(chat)
        return chat
    return None


def get_pending_chats(*, session: Session, skip: int = 0, limit: int = 100) -> list[SupportChat]:
    statement = select(SupportChat).where(
        SupportChat.status == ChatStatus.pending
    ).order_by(SupportChat.created_at.desc()).offset(skip).limit(limit)
    return list(session.exec(statement).all())


# =============================================================================
# Message Map CRUD Operations
# =============================================================================

def create_message_map(*, session: Session, message_map: MessageMapCreate) -> MessageMap:
    db_obj = MessageMap.model_validate(message_map)
    session.add(db_obj)
    session.commit()
    session.refresh(db_obj)
    return db_obj


def get_message_map_by_user_msg(
    *, session: Session, chat_id: uuid.UUID, user_message_id: int
) -> MessageMap | None:
    statement = select(MessageMap).where(
        MessageMap.chat_id == chat_id,
        MessageMap.user_message_id == user_message_id
    )
    return session.exec(statement).first()


def get_message_map_by_support_msg(
    *, session: Session, chat_id: uuid.UUID, support_message_id: int
) -> MessageMap | None:
    statement = select(MessageMap).where(
        MessageMap.chat_id == chat_id,
        MessageMap.support_message_id == support_message_id
    )
    return session.exec(statement).first()
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item
