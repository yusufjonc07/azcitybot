from aiogram import Dispatcher

from app.bot_client.commands import set_default_commands
from app.bot_client.handlers.routers import admin_router, user_router
from app.bot_client.middlewares import setup_middlewares


async def setup_routes(dp: Dispatcher):
    dp.include_router(user_router)
    dp.include_router(admin_router)


__all__ = ["setup_middlewares", "setup_routes", "set_default_commands"]
