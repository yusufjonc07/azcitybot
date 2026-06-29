from aiogram import Dispatcher
from aiogram.dispatcher.event.bases import UNHANDLED
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import ExceptionTypeFilter
from aiogram.types import ErrorEvent

from utils import logger

from .commands import set_default_commands
from .handlers.routers import admin_router, user_router
from .middlewares import setup_middlewares


# Benign Telegram API errors that mean "nothing to do" rather than a real bug.
# Editing a message to identical content, acting on a deleted/expired message,
# or answering a stale callback should be ignored — not logged as crashes nor
# forwarded to the admin error chat.
_BENIGN_TELEGRAM_ERRORS = (
    "message is not modified",
    "message to edit not found",
    "message can't be edited",
    "message to delete not found",
    "query is too old",
    "MESSAGE_ID_INVALID",
)


async def _ignore_benign_telegram_errors(event: ErrorEvent):
    text = str(event.exception)
    if any(fragment in text for fragment in _BENIGN_TELEGRAM_ERRORS):
        logger.info(f"Ignored benign Telegram error: {event.exception}")
        return True  # handled -> swallow
    return UNHANDLED  # real error -> propagate to server.py notify_error


async def setup_routes(dp: Dispatcher):
    # Global error handler: only TelegramBadRequest reaches it; benign ones are
    # swallowed, everything else propagates unchanged.
    dp.errors.register(_ignore_benign_telegram_errors, ExceptionTypeFilter(TelegramBadRequest))
    dp.include_router(user_router)
    dp.include_router(admin_router)


__all__ = ["setup_middlewares", "setup_routes"]
