from aiogram.dispatcher.event.telegram import TelegramEventObserver
from aiogram.types import Message, CallbackQuery, InlineQuery

from app.bot_client.loader import i18n
from app.models import User


async def i18n_middleware(event: TelegramEventObserver):
    @event.middleware()
    async def process(handler, event: Message | CallbackQuery | InlineQuery, data):
        user: User = data.get("user")
        if user:
            i18n.ctx_locale.set(user.lang)
        await handler(event, data)
