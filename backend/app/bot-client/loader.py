from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.utils.i18n import I18n
from aiogram.fsm.storage.memory import MemoryStorage

from app.core.config import settings

bot = Bot(
    settings.TELEGRAM_BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML, link_preview_is_disabled=True),
)

storage = MemoryStorage()
dp = Dispatcher(storage=storage)

i18n = I18n(path=settings.I18N_PATH, domain=settings.I18N_DOMAIN)
_ = i18n.gettext
