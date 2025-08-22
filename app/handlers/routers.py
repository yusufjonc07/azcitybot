from aiogram import Router

from .users.start import router as start_router
from .users.lang import router as lang_router
from .users.chat import router as chat_router

from .admins.join import router as join_router
from .admins.claim import router as claim_router
from .admins.notify import router as notify_router
from .admins.reply import router as reply_router
from .admins.users import router as users_router


user_router = Router()
user_router.include_router(start_router)
user_router.include_router(lang_router)
user_router.include_router(chat_router)

admin_router = Router()
admin_router.include_router(join_router)
admin_router.include_router(claim_router)
# admin_router.include_router(notify_router)
admin_router.include_router(reply_router)
admin_router.include_router(users_router)
