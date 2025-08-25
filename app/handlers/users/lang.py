from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.keyboards import LangKeyboard
from database.models import User
from loader import _

router = Router()

@router.message(Command("lang"))
async def _lang(message: Message):
    await message.answer(_("Select language:"), reply_markup=LangKeyboard.keyboard())

@router.callback_query(LangKeyboard.filter())
async def _lang_callback(call: CallbackQuery, callback_data: LangKeyboard.Callback):
    await call.answer("Processing...", show_alert=False)
    await call.message.edit_text(
        _("welcome_message", locale=callback_data.lang),
    )

    try:
        await User.update(call.from_user.id, lang=callback_data.lang)
    except Exception as e:
        print(f"Error updating user language: {e}")

