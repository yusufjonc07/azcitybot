"""
Chat message models for web-based support chat.
These store actual message content for the dashboard chat interface.
"""
import uuid
from datetime import datetime
from enum import Enum

from sqlalchemy import BigInteger, Column, Text
from sqlmodel import Field, Relationship, SQLModel


class WebMessageType(str, Enum):
    text = "text"
    image = "image"
    file = "file"
    sticker = "sticker"
    voice = "voice"
    video = "video"
    system = "system"


class WebMessageBase(SQLModel):
    content: str = Field(sa_column=Column(Text))
    message_type: WebMessageType = Field(default=WebMessageType.text)
    file_url: str | None = Field(default=None, max_length=1024)
    file_name: str | None = Field(default=None, max_length=255)
    file_size: int | None = Field(default=None)
    is_from_user: bool = Field(default=True)  # True = user sent, False = admin sent
    is_read: bool = Field(default=False)


class WebMessageCreate(SQLModel):
    support_chat_id: uuid.UUID
    content: str
    message_type: WebMessageType = WebMessageType.text
    file_url: str | None = None
    file_name: str | None = None
    file_size: int | None = None
    is_from_user: bool = True
    sender_id: uuid.UUID | None = None  # User ID of the sender


class WebMessageUpdate(SQLModel):
    is_read: bool | None = None
    content: str | None = None


# Import here to avoid circular imports
from app.models import SupportChat


class WebMessage(WebMessageBase, table=True):
    __tablename__ = "web_message"
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    support_chat_id: uuid.UUID = Field(
        foreign_key="support_chat.id", nullable=False, ondelete="CASCADE"
    )
    sender_id: uuid.UUID | None = Field(
        default=None, foreign_key="user.id", ondelete="SET NULL"
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Relationships will be added dynamically to avoid circular imports


class WebMessagePublic(WebMessageBase):
    id: uuid.UUID
    support_chat_id: uuid.UUID
    sender_id: uuid.UUID | None
    created_at: datetime


class WebMessagesPublic(SQLModel):
    data: list[WebMessagePublic]
    count: int


# Extended SupportChat response with user info and last message
class SupportChatWithUser(SQLModel):
    id: uuid.UUID
    status: str
    created_at: datetime
    updated_at: datetime | None
    claimed_at: datetime | None
    user_id: uuid.UUID
    admin_id: uuid.UUID | None
    # User info
    user_telegram_id: int
    user_full_name: str | None
    user_username: str | None
    user_photo_url: str | None
    # Last message info
    last_message: str | None
    last_message_time: datetime | None
    unread_count: int


class SupportChatsWithUsersPublic(SQLModel):
    data: list[SupportChatWithUser]
    count: int
