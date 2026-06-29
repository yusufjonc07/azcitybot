from aiogram.dispatcher.event.telegram import TelegramEventObserver
from aiogram.types import Message, CallbackQuery, InlineQuery

from database.models import User


async def status_middleware(event: TelegramEventObserver):
    @event.middleware()
    async def process(handler, event: Message | CallbackQuery | InlineQuery, data):
        user: User = data.get("user")
        # is_admin() covers both admin and super_admin (the old `!= "admin"`
        # check locked super_admins out of every admin handler).
        if not user or not user.is_admin():
            return
        return await handler(event, data)
