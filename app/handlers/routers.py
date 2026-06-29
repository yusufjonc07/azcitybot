from aiogram import Router


from app.handlers.admins.claim import router as claim_router
from app.handlers.admins.reply import router as reply_router
from app.handlers.admins.edit import router as edit_router
from app.handlers.admins.users import router as users_router
from app.handlers.admins.notify import router as notify_router

from app.handlers.users.start import router as start_router
from app.handlers.users.lang import router as lang_router
from app.handlers.users.chat import router as chat_router

admin_router = Router()
admin_router.include_router(claim_router)
admin_router.include_router(reply_router)
admin_router.include_router(edit_router)
admin_router.include_router(users_router)
admin_router.include_router(notify_router)

user_router = Router()
user_router.include_router(start_router)
user_router.include_router(lang_router)
user_router.include_router(chat_router)
