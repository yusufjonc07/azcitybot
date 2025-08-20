from aiogram.filters import Command
from aiogram.types import Message

from app.handlers.routers import user_router as router
from app.keyboards.lang import LangKeyboard
from loader import _


@router.message(Command("start"))
async def start_cmd(message: Message):
    choosing_label = "\n".join([
        "🇺🇿 Iltmos tilni tanlang:",
        "🇬🇧 Please choose your language:",
        "🇷🇺 Пожалуйста, выберите ваш язык:",
        "🇰🇷 언어 선택:",
    ])

    await message.answer(choosing_label, reply_markup=LangKeyboard.keyboard())