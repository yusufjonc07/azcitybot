import uuid
from typing import Any

from sqlmodel import Session, select

from app.models import Item, ItemCreate, User, UserCreate, UserUpdate


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
    )
    return create_user(session=session, user_create=user_create)


def create_item(*, session: Session, item_in: ItemCreate, owner_id: uuid.UUID) -> Item:
    db_item = Item.model_validate(item_in, update={"owner_id": owner_id})
    session.add(db_item)
    session.commit()
    session.refresh(db_item)
    return db_item
