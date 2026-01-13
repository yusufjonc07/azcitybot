"""
Admin claim handler for support chats.
Uses PostgreSQL for database operations.
"""
from datetime import datetime
from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.exceptions import TelegramForbiddenError
from sqlmodel import select

from app.bot_client.keyboards.chat import ClaimChatKeyboard, EndChatKeyboard
from app.bot_client.loader import _
from app.bot_client.database import get_session
from app.bot_client.services.user_service import UserService
from app.bot_client.services.chat_service import ChatService
from app.models import User, SupportChat, SupportChatUpdate, ChatStatus, MessageMap, UserUpdate
import logging

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(ClaimChatKeyboard.Callback.filter())
async def _claim(callback: CallbackQuery, callback_data: ClaimChatKeyboard.Callback):
    """Admin claims a pending chat."""
    await callback.answer()
    
    admin_telegram_id = callback.from_user.id
    client_telegram_id = int(callback_data.data)

    with get_session() as session:
        # Get admin user
        admin = UserService.get_by_telegram_id(session, admin_telegram_id)
        if not admin or not admin.is_admin():
            await callback.answer(_('You are not an admin.'), show_alert=True)
            return

        # Check admin has groups
        group_ids = admin.admin_groups or []
        if not group_ids:
            await callback.answer(_('No group connected to your admin account.'), show_alert=True)
            return

        # Find the pending chat
        client_user = UserService.get_by_telegram_id(session, client_telegram_id)
        if not client_user:
            await callback.answer(_('Client not found.'), show_alert=True)
            return

        statement = select(SupportChat).where(
            SupportChat.user_id == client_user.id,
            SupportChat.status == ChatStatus.pending,
            SupportChat.notified_message_id != None
        )
        chat = session.exec(statement).first()

        if not chat or chat.status != ChatStatus.pending:
            return

        # Find the best group to use
        # Check if client had a previous chat with one of the admin's groups
        statement = select(SupportChat).where(
            SupportChat.user_id == client_user.id,
            SupportChat.support_group_id.in_([int(g) for g in group_ids])
        )
        former_chat = session.exec(statement).first()

        if former_chat and former_chat.support_group_id:
            to_group_id = former_chat.support_group_id
        else:
            # Find group with least active chats
            group_loads = {}
            for gid in group_ids:
                statement = select(SupportChat).where(
                    SupportChat.support_group_id == int(gid),
                    SupportChat.status == ChatStatus.active
                )
                count = len(session.exec(statement).all())
                group_loads[gid] = count

            if all(v == 0 for v in group_loads.values()):
                to_group_id = int(group_ids[0])
            else:
                to_group_id = int(min(group_loads, key=group_loads.get))

        try:
            # Notify the group
            notice_sent = await callback.bot.send_message(
                chat_id=to_group_id,
                text="#muloqotda\n✅ <b>{name}</b> ({id}) \n @{username} \n mijoz qabul qilindi\n💬 Suhbat shu yerda davom etadi...\n\n".format(
                    name=client_user.full_name,
                    id=client_user.telegram_id,
                    username=client_user.username or "username yo'q"
                ),
                parse_mode="HTML",
                reply_markup=EndChatKeyboard.keyboard(chatId=str(chat.id))
            )
        except TelegramForbiddenError:
            # Bot was kicked from the support group - remove it from admin's groups
            group_ids = [g for g in group_ids if g != str(to_group_id)]
            UserService.update(session, admin, UserUpdate(
                admin_groups=group_ids,
                status=admin.status if group_ids else "user"
            ))
            # Retry claim process
            await _claim(callback, callback_data)
            return

        # Update chat: set admin_id, support_group_id, status, claimed_at
        ChatService.update(session, chat, SupportChatUpdate(
            admin_id=admin.id,
            support_group_id=to_group_id,
            status=ChatStatus.active,
            notice_message_id=notice_sent.message_id,
        ))

        # Create initial message mapping
        msg_map = MessageMap(
            chat_id=chat.id,
            user_message_id=0,  # No specific user message
            support_message_id=notice_sent.message_id,
        )
        session.add(msg_map)
        session.commit()

        # Forward pending messages to the group
        for msg_id in chat.pending_message_ids or []:
            try:
                sent = await callback.bot.copy_message(
                    chat_id=to_group_id,
                    from_chat_id=client_user.telegram_id,
                    message_id=msg_id,
                    reply_to_message_id=notice_sent.message_id
                )

                # Store message mapping
                msg_map = MessageMap(
                    chat_id=chat.id,
                    user_message_id=msg_id,
                    support_message_id=sent.message_id,
                )
                session.add(msg_map)
                session.commit()

            except Exception as e:
                logger.error(f"Failed to copy message {msg_id}: {e}")

        # Get support group info
        support_group = await callback.bot.get_chat(to_group_id)

        # Update the general group message
        await callback.message.edit_text(
            text="#muloqotda\n✅ <b>{name}</b> ({id}) \n @{username} \n mijoz qabul qilindi\n💬 Suhbat <b>{group_name}</b>da davom etadi...".format(
                name=client_user.full_name,
                id=client_user.telegram_id,
                username=client_user.username or "username yo'q",
                group_name=support_group.title
            ),
            reply_markup=None,
            parse_mode="HTML"
        )
        await callback.answer(_('You have claimed this chat.'), show_alert=True)
