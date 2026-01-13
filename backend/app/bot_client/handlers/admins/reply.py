"""
Admin reply handler for support chats.
Uses PostgreSQL for database operations.
"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from sqlmodel import select

from app.bot_client.loader import _
from app.bot_client.database import get_session
from app.bot_client.services.user_service import UserService
from app.bot_client.keyboards.chat import ChooseToSend
from app.models import User, SupportChat, ChatStatus, MessageMap
import logging

logger = logging.getLogger(__name__)

router = Router()


# --- ADMIN REPLY HANDLER (text + media) ---
@router.message(F.chat.type.in_({"group", "supergroup"}), ~F.text.startswith("/"))
async def admin_reply(message: Message, user_id: int = None):
    """Handle admin replies in support groups."""
    
    with get_session() as session:
        # Check if this chat is one of the admin groups
        statement = select(User).where(
            User.admin_groups.contains([str(message.chat.id)])
        )
        is_admin_group = session.exec(statement).first()

        if not is_admin_group:
            return

        if user_id:
            pass
        elif message.reply_to_message is not None:
            # Find the original user from message mapping
            statement = select(MessageMap).where(
                MessageMap.support_message_id == message.reply_to_message.message_id
            )
            # Need to join with chat to filter by group
            from app.models import SupportChat
            statement = select(MessageMap, SupportChat).join(
                SupportChat, MessageMap.chat_id == SupportChat.id
            ).where(
                SupportChat.support_group_id == message.chat.id,
                MessageMap.support_message_id == message.reply_to_message.message_id
            )
            result = session.exec(statement).first()

            if not result:
                await message.reply(_(f"Cannot find the original user for this reply."))
                return

            mapping, chat = result
            user = chat.user
            if user:
                user_id = user.telegram_id
            else:
                return
        else:
            # Find active chats in this group
            statement = select(SupportChat).where(
                SupportChat.support_group_id == message.chat.id,
                SupportChat.status == ChatStatus.active
            )
            chats = session.exec(statement).all()

            if len(chats) == 0:
                await message.reply(_("Bu chat uchun faol suhbat topilmadi."))
                return

            elif len(chats) > 1:
                # Multiple active chats - ask admin to choose
                users = []
                for c in chats:
                    if c.user:
                        users.append((c.user.telegram_id, c.user.full_name))

                await message.reply(
                    _("Bu chat uchun bir nechta faol suhbat topildi. \nYuborish uchun mijozni tanlang:"),
                    reply_markup=ChooseToSend.keyboard(users)
                )
                return
            else:
                user = chats[0].user
                if user:
                    user_id = user.telegram_id
                else:
                    return

        try:
            sent = await message.bot.copy_message(
                chat_id=user_id,
                from_chat_id=message.chat.id,
                message_id=message.message_id
            )

            # Store message mapping for edit support (admin->user)
            if sent:
                # Find the active chat for this user
                db_user = UserService.get_by_telegram_id(session, user_id)
                if db_user:
                    statement = select(SupportChat).where(
                        SupportChat.user_id == db_user.id,
                        SupportChat.support_group_id == message.chat.id,
                        SupportChat.status == ChatStatus.active
                    )
                    chat = session.exec(statement).first()
                    if chat:
                        msg_map = MessageMap(
                            chat_id=chat.id,
                            user_message_id=sent.message_id,
                            support_message_id=message.message_id,
                        )
                        session.add(msg_map)
                        session.commit()

        except Exception as e:
            logger.error(f"Failed to send to user {user_id}: {e}")


@router.callback_query(ChooseToSend.Callback.filter())
async def _choose_to_send(call: CallbackQuery, callback_data: ChooseToSend.Callback):
    """Handle admin choosing which user to send to."""
    await call.answer()

    user_id = int(callback_data.data)
    message = call.message.reply_to_message

    with get_session() as session:
        user = UserService.get_by_telegram_id(session, user_id)
        if not user:
            await call.answer(_("Foydalanuvchi topilmadi."), show_alert=True)
            return

        await admin_reply(message, user_id=user_id)
        await call.message.edit_reply_markup(reply_markup=None)
        await call.message.edit_text(f"{user.full_name} ({user.telegram_id}) ga yuborildi.")
