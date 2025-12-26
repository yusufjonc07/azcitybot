from enum import Enum

from pydantic import Field, field_validator

from database.base import Base


class Status(Enum):
    banned = 0
    user = 1
    admin = 2
    super_admin = 3


class User(Base):
    id: int = Field(default_factory=int, alias="_id")
    name: str
    username: str | None = None
    fullname: str | None = None
    status: str = "user"
    admin_groups: list[str] = Field(default_factory=list)
    lang: str

    _status_enum = Status

    # --- Validators ---

    @field_validator("admin_groups", mode="before")
    @classmethod
    def normalize_admin_groups(cls, v):
        return v or []

    @field_validator("status", mode="before")
    @classmethod
    def validate_status(cls, v):
        if isinstance(v, Status):
            return v.name
        if v not in Status.__members__:
            return Status.user.name
        return v

    # --- Business logic ---

    def is_admin(self, super: bool = False) -> bool:
        if super:
            return self.status == Status.super_admin.name
        return self.status in (
            Status.admin.name,
            Status.super_admin.name,
        )

    def statuses_to_edit(self, status: str) -> list[str]:
        self_value = self._status_enum[self.status].value
        target_value = self._status_enum[status].value

        if target_value >= self_value:
            return []

        return [
            s.name
            for s in self._status_enum
            if s.value < self_value
        ]

    # --- DB helpers ---

    @classmethod
    async def get_or_create(
        cls,
        id: int,
        name: str,
        username: str | None,
        lang: str,
    ):
        user = await cls.get(id)

        if user:
            return await cls.update(
                user.id,
                name=name,
                username=username,
            )

        return await cls.create(
            _id=id,
            name=name,
            username=username,
            lang=lang,
        )


User.set_collection("users")
