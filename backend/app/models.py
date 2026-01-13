import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, Column, JSON
from sqlmodel import Field, Relationship, SQLModel


# =============================================================================
# Enums
# =============================================================================

class UserStatus(str, Enum):
    banned = "banned"
    user = "user"
    admin = "admin"
    super_admin = "super_admin"


class ChatStatus(str, Enum):
    pending = "pending"
    active = "active"
    cancelled = "cancelled"
    finished = "finished"


# =============================================================================
# User Models (unified for web dashboard and Telegram bot)
# =============================================================================

# Shared properties
class UserBase(SQLModel):
    telegram_id: int = Field(sa_column=Column(BigInteger, unique=True, index=True))
    username: str | None = Field(default=None, max_length=255)
    full_name: str | None = Field(default=None, max_length=255)
    photo_url: str | None = Field(default=None, max_length=512)
    is_active: bool = True
    is_superuser: bool = False
    # Bot-specific fields
    status: UserStatus = Field(default=UserStatus.user)
    lang: str = Field(default="uz", max_length=10)
    admin_groups: list[str] = Field(default_factory=list, sa_column=Column(JSON))


# Properties to receive via API on creation (from Telegram login)
class UserCreate(SQLModel):
    telegram_id: int
    username: str | None = None
    full_name: str | None = None
    photo_url: str | None = None
    lang: str = "uz"


# Properties to receive via API on update, all are optional
class UserUpdate(SQLModel):
    username: str | None = None
    full_name: str | None = None
    photo_url: str | None = None
    is_active: bool | None = None
    is_superuser: bool | None = None
    status: UserStatus | None = None
    lang: str | None = None
    admin_groups: list[str] | None = None


class UserUpdateMe(SQLModel):
    full_name: str | None = Field(default=None, max_length=255)


# Database model, database table inferred from class name
class User(UserBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    chats: list["Chat"] = Relationship(back_populates="owner", cascade_delete=True)
    # Support chat relationships
    support_chats: list["SupportChat"] = Relationship(
        back_populates="user",
        sa_relationship_kwargs={"foreign_keys": "SupportChat.user_id"}
    )
    
    def is_admin(self, super_only: bool = False) -> bool:
        """Check if user has admin privileges."""
        if super_only:
            return self.status == UserStatus.super_admin
        return self.status in (UserStatus.admin, UserStatus.super_admin)


# Properties to return via API, id is always required
class UserPublic(UserBase):
    id: uuid.UUID
    created_at: datetime


class UsersPublic(SQLModel):
    data: list[UserPublic]
    count: int


# Shared properties
class ChatBase(SQLModel):
    title: str = Field(min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=255)


# Properties to receive on chat creation
class ChatCreate(ChatBase):
    pass


# Properties to receive on chat update
class ChatUpdate(ChatBase):
    title: str | None = Field(default=None, min_length=1, max_length=255)  # type: ignore


# Database model, database table inferred from class name
class Chat(ChatBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    owner_id: uuid.UUID = Field(
        foreign_key="user.id", nullable=False, ondelete="CASCADE"
    )
    owner: User | None = Relationship(back_populates="chats")


# Properties to return via API, id is always required
class ChatPublic(ChatBase):
    id: uuid.UUID
    owner_id: uuid.UUID


class ChatsPublic(SQLModel):
    data: list[ChatPublic]
    count: int


# Generic message
class Message(SQLModel):
    message: str


# JSON payload containing access token
class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


# Contents of JWT token
class TokenPayload(SQLModel):
    sub: str | None = None


# Telegram Login Data
class TelegramLoginData(SQLModel):
    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    photo_url: str | None = None
    auth_date: int
    hash: str


# Telegram WebApp Init Data
class TelegramWebAppData(SQLModel):
    init_data: str


# =============================================================================
# Support Chat Models (for bot conversations)
# =============================================================================

class SupportChatBase(SQLModel):
    status: ChatStatus = Field(default=ChatStatus.pending)
    notified_message_id: int | None = Field(default=None, sa_column=Column(BigInteger))
    notice_message_id: int | None = Field(default=None, sa_column=Column(BigInteger))
    support_group_id: int | None = Field(default=None, sa_column=Column(BigInteger))
    pending_message_ids: list[int] = Field(default_factory=list, sa_column=Column(JSON))


class SupportChatCreate(SQLModel):
    user_id: uuid.UUID
    notified_message_id: int | None = None


class SupportChatUpdate(SQLModel):
    status: ChatStatus | None = None
    admin_id: uuid.UUID | None = None
    notified_message_id: int | None = None
    notice_message_id: int | None = None
    support_group_id: int | None = None
    pending_message_ids: list[int] | None = None


class SupportChat(SupportChatBase, table=True):
    __tablename__ = "support_chat"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", nullable=False, ondelete="CASCADE")
    admin_id: uuid.UUID | None = Field(default=None, foreign_key="user.id", ondelete="SET NULL")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime | None = Field(default=None)
    claimed_at: datetime | None = Field(default=None)
    cancelled_at: datetime | None = Field(default=None)
    finished_at: datetime | None = Field(default=None)
    
    # Relationships
    user: User | None = Relationship(
        back_populates="support_chats",
        sa_relationship_kwargs={"foreign_keys": "[SupportChat.user_id]"}
    )
    messages: list["MessageMap"] = Relationship(back_populates="chat", cascade_delete=True)


class SupportChatPublic(SupportChatBase):
    id: uuid.UUID
    user_id: uuid.UUID
    admin_id: uuid.UUID | None
    created_at: datetime


# =============================================================================
# Message Map Models (for tracking messages between user and support group)
# =============================================================================

class MessageMapBase(SQLModel):
    user_message_id: int = Field(sa_column=Column(BigInteger))
    support_message_id: int = Field(sa_column=Column(BigInteger))


class MessageMapCreate(SQLModel):
    chat_id: uuid.UUID
    user_message_id: int
    support_message_id: int


class MessageMap(MessageMapBase, table=True):
    __tablename__ = "message_map"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    chat_id: uuid.UUID = Field(foreign_key="support_chat.id", nullable=False, ondelete="CASCADE")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships
    chat: SupportChat | None = Relationship(back_populates="messages")