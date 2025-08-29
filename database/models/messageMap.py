from pydantic import Field
from database.base import Base

class MessageMap(Base):
	id: str = Field(default_factory=str, alias="_id")
	user_id: int  # Telegram user id
	user_msg_id: int  # Message id in user's private chat
	group_id: int  # Group or admin group id
	group_msg_id: int  # Message id in group/admin group
	direction: str  # 'user_to_group' or 'group_to_user'
	created_at: int | None = None

MessageMap.set_collection("message_maps")
