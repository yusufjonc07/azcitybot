from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.bot_client.keyboards.lang import LangKeyboard
from app.bot_client.keyboards.chat import ClaimChatKeyboard
from app.bot_client.loader import _
from app.bot_client.database import get_session
from app.bot_client.services.user_service import UserService
from app.bot_client.services.chat_service import ChatService
from app.core.config import settings
from app.models import ChatStatus

router = Router()


# /admin command handler - add user as admin for a group
@router.message(Command("admin"), F.chat.type.in_({"group", "supergroup"}))
async def _admin(message: Message):
    # Parse username from message.text
    parts = message.text.strip().split()
    if len(parts) < 2 or not parts[1].startswith("@"):
        await message.reply(_("Usage: /admin @username"))
        return
    
    username = parts[1].lstrip("@")
    
    with get_session() as session:
        # Find user by username
        from sqlmodel import select
        from app.models import User
        statement = select(User).where(User.username == username)
        user = session.exec(statement).first()
        
        if not user:
            await message.reply(_(f"User @{username} not found in the bot database."))
            return
        
        group_id = str(message.chat.id)
        admin_groups = list(user.admin_groups or [])
        
        if group_id not in admin_groups:
            admin_groups.append(group_id)
            from app.bot_client.services.user_service import UserService
            from app.models import UserUpdate, UserStatus
            UserService.update(session, user, UserUpdate(admin_groups=admin_groups, status=UserStatus.admin))
            await message.reply(_(f"@{username} is now an admin for this group!"))
        else:
            await message.reply(_(f"@{username} is already an admin for this group."))


# /pending command handler - show pending chats
@router.message(Command("pending"), F.chat.type.in_({"group", "supergroup"}))
async def _pending_chats(message: Message):
    if str(message.chat.id) != str(settings.SUPPORT_GROUP_ID):
        await message.reply(_("This command can only be used in the support group."))
        return
    
    with get_session() as session:
        from sqlmodel import select
        from app.models import SupportChat
        statement = select(SupportChat).where(SupportChat.status == ChatStatus.pending)
        pending_chats = session.exec(statement).all()
        
        if len(pending_chats) == 0:
            await message.reply("Kutayotgan mijozlar yo'q. ✅")
            return
        
        for chat in pending_chats:
            if chat.notified_message_id:
                try:
                    resent_msg = await message.bot.copy_message(
                        chat_id=settings.SUPPORT_GROUP_ID,
                        from_chat_id=settings.SUPPORT_GROUP_ID,
                        message_id=chat.notified_message_id,
                        reply_markup=ClaimChatKeyboard.keyboard(chat.user.telegram_id)
                    )
                    
                    # Delete the old notified message
                    await message.bot.delete_message(
                        chat_id=settings.SUPPORT_GROUP_ID,
                        message_id=chat.notified_message_id
                    )
                    
                    # Update the chat with new notified_message_id
                    from app.models import SupportChatUpdate
                    ChatService.update(session, chat, SupportChatUpdate(notified_message_id=resent_msg.message_id))
                except Exception:
                    continue


@router.message(Command("lang"))
async def _lang(message: Message):
    await message.answer(_("Select language:"), reply_markup=LangKeyboard.keyboard())


@router.callback_query(LangKeyboard.filter())
async def _lang_callback(call: CallbackQuery, callback_data: LangKeyboard.Callback):
    await call.answer("Processing...", show_alert=False)
    
    await call.message.edit_text(
        _("welcome_message", locale=callback_data.lang), parse_mode="HTML",
    )

    with get_session() as session:
        UserService.get_or_create(
            session,
            telegram_id=call.from_user.id,
            full_name=call.from_user.full_name,
            username=call.from_user.username,
            lang=callback_data.lang,
        )

