from datetime import datetime
from enum import Enum

from bson import ObjectId
from pydantic import Field

from database.base import Base


class Status(Enum):
    pending = 0
    active = 1
    cancelled = 2
    finished = 3


class Chat(Base):
    id: int = Field(default_factory=int, alias="_id")
    user_id: int
    created_at: int
    admin_id: int | None = None
    updated_at: int | None = None
    claimed_at: int | None = None
    cancelled_at: int | None = None
    finished_at: int | None = None
    status: str = Field(default="pending")
    notificated_message_id: int | None = None
    last_message_id: int | None = None
    support_group_id: int | None = None

    _status: Status = Status

    def statuses_to_edit(self, status: str) -> list[str]:
        self_status = getattr(self._status, self.status).value
        status = getattr(self._status, status).value
        return [] if status >= self_status else [i.name for i in self._status if i.value < self_status]


    @classmethod
    async def get_or_create(cls, id: int, name: str, username: str | None, lang: str):
        user = await cls.get(id)
        user = (
            await cls.update(user.id, name=name, username=username)
            if user
            else await cls.create(_id=id, name=name, username=username, lang=lang)
        )
        return user
    
    @classmethod
    async def add(cls, user_id: int):
        print("adding chat")
        pending_chats = await cls._collection.find_one({
            "user_id": user_id,
            "status": "pending",
            "notificated_message_id": {"$ne": None}
        })

        print("checking chat")

        if not pending_chats:
            print("no pending chats found")
            chat = await cls.create(
                id=str(ObjectId()),
                user_id=user_id,
                created_at=int(datetime.now().timestamp())
            )
            return chat
        else:
            raise ValueError("User already has a pending chat")

Chat.set_collection("chats")
