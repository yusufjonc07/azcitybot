import csv
import io

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message
from database.models import User

router = Router()

@router.message(Command("users"))
async def _users(message: Message):
    file = await _get_users_data()
    await message.answer_document(BufferedInputFile(file, "users.csv"))


async def _get_users_data():
    file = io.StringIO()
    writer = csv.writer(file)
    writer.writerow(list(User.__annotations__.keys()))
    for user in await User.get_all():
        writer.writerow(list(user.dict().values()))
    file.seek(0)
    file = io.BytesIO(file.getvalue().encode())
    file.seek(0)
    return file.getvalue()
