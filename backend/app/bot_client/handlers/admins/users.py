"""
Admin users handler - export bot users.
Uses PostgreSQL for database operations.
"""
import csv
import io

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import BufferedInputFile, Message
from sqlmodel import select

from app.bot_client.database import get_session
from app.models import User

router = Router()


@router.message(Command("users"))
async def _users(message: Message):
    """Export all bot users as CSV."""
    file = await _get_users_data()
    await message.answer_document(BufferedInputFile(file, "users.csv"))


async def _get_users_data() -> bytes:
    """Generate CSV with all bot users."""
    with get_session() as session:
        statement = select(User)
        users = session.exec(statement).all()

        file = io.StringIO()
        writer = csv.writer(file)
        
        # Write header
        writer.writerow([
            "id", "telegram_id", "username", "full_name", 
            "status", "lang", "created_at"
        ])
        
        # Write user data
        for user in users:
            writer.writerow([
                str(user.id),
                user.telegram_id,
                user.username or "",
                user.full_name or "",
                user.status.value if user.status else "",
                user.lang,
                user.created_at.isoformat() if user.created_at else "",
            ])
        
        file.seek(0)
        return file.getvalue().encode()
