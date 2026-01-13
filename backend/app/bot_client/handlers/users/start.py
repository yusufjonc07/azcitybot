from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.bot_client.keyboards.lang import LangKeyboard
from app.bot_client.loader import _

router = Router()

@router.message(Command("start"))
async def start_cmd(message: Message):
    choosing_label = "\n".join([
        "🇺🇿 Iltmos tilni tanlang:",
        "🇷🇺 Пожалуйста, выберите ваш язык:",
        "🇰🇷 언어 선택:",
    ])

    await message.answer(choosing_label, reply_markup=LangKeyboard.keyboard())