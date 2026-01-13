from aiogram.dispatcher.event.telegram import TelegramEventObserver
from aiogram.types import CallbackQuery, InlineQuery, Message

from app.bot_client.database import get_session
from app.bot_client.services.user_service import UserService
from app.models import User


async def user_middleware(event: TelegramEventObserver):
    @event.middleware()
    async def process(handler, event: Message | CallbackQuery | InlineQuery, data):
        await process_user(event.from_user, data)
        await handler(event, data)

    async def process_user(from_user, data):
        with get_session() as session:
            data["user"] = UserService.get_or_create(
                session,
                telegram_id=from_user.id,
                full_name=from_user.full_name,
                username=from_user.username,
                lang="uz"
            )
