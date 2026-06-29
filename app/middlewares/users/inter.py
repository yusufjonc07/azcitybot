from aiogram.dispatcher.event.telegram import TelegramEventObserver
from aiogram.types import Message, CallbackQuery, InlineQuery

from database.models import User
from loader import i18n


async def i18n_middleware(event: TelegramEventObserver):
    @event.middleware()
    async def process(handler, event: Message | CallbackQuery | InlineQuery, data):
        user: User = data.get("user")
        i18n.ctx_locale.set(user.lang if user else "uz")
        return await handler(event, data)
