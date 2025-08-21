from aiogram import Dispatcher

from .commands import set_default_commands
from .handlers.routers import user_router, admin_router
from .middlewares import setup_middlewares


async def setup_routes(dp: Dispatcher):
    dp.include_router(user_router)
    dp.include_router(admin_router)


__all__ = ["setup_middlewares", "setup_routes"]
