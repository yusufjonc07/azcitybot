"""
User service for bot operations with PostgreSQL.
"""
from uuid import UUID

from sqlmodel import Session, select

from app.models import User, UserCreate, UserUpdate, UserStatus


class UserService:
    """Service for bot user database operations."""

    @staticmethod
    def get_by_telegram_id(session: Session, telegram_id: int) -> User | None:
        """Get user by Telegram ID."""
        statement = select(User).where(User.telegram_id == telegram_id)
        return session.exec(statement).first()

    @staticmethod
    def get_by_id(session: Session, user_id: UUID) -> User | None:
        """Get user by internal ID."""
        return session.get(User, user_id)

    @staticmethod
    def create(session: Session, user_in: UserCreate) -> User:
        """Create a new user."""
        db_user = User.model_validate(user_in)
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user

    @staticmethod
    def update(session: Session, db_user: User, user_in: UserUpdate) -> User:
        """Update a user."""
        user_data = user_in.model_dump(exclude_unset=True)
        db_user.sqlmodel_update(user_data)
        session.add(db_user)
        session.commit()
        session.refresh(db_user)
        return db_user

    @staticmethod
    def get_or_create(
        session: Session,
        telegram_id: int,
        full_name: str,
        username: str | None = None,
        lang: str = "uz",
    ) -> User:
        """Get existing user or create a new one."""
        user = UserService.get_by_telegram_id(session, telegram_id)
        
        if user:
            # Update user info if changed
            update_data = UserUpdate(full_name=full_name, username=username)
            return UserService.update(session, user, update_data)
        
        # Create new user
        user_in = UserCreate(
            telegram_id=telegram_id,
            full_name=full_name,
            username=username,
            lang=lang,
        )
        return UserService.create(session, user_in)

    @staticmethod
    def update_language(session: Session, telegram_id: int, lang: str) -> User | None:
        """Update user's language preference."""
        user = UserService.get_by_telegram_id(session, telegram_id)
        if user:
            return UserService.update(session, user, UserUpdate(lang=lang))
        return None
