from aiogram import Router
from aiogram.types import CallbackQuery
from app.keyboards.chat import ClaimChatKeyboard, EndChatKeyboard
from database.models import Chat, User
from loader import _
from database.models.messageMap import MessageMap
from datetime import datetime
from aiogram.exceptions import TelegramForbiddenError
from utils import logger

router = Router()


@router.callback_query(ClaimChatKeyboard.Callback.filter())
async def _claim(callback: CallbackQuery, callback_data: ClaimChatKeyboard.Callback):

    await callback.answer()
    user_id = callback.from_user.id
    chat_user_id = int(callback_data.data)
    admin = await User.get(user_id)
    if not admin or not admin.is_admin():
        await callback.answer(_('You are not an admin.'), show_alert=True)
        return
    # admin_groups is stored on the admin user document. Copy it so list
    # mutation (dropping a forbidden group) doesn't touch the cached model.
    group_ids = list(getattr(admin, 'admin_groups', None) or [])
    if not group_ids:
        await callback.answer(_('No group connected to your admin account.'), show_alert=True)
        return

    # Find the pending chat
    chat = await Chat._collection.find_one({
        'user_id': chat_user_id,
        'status': 'pending',
        'notificated_message_id': {'$ne': None}
    })
    if not chat:
        return

    if chat['status'] != 'pending':
        return

    client_user = await User.get(chat_user_id)
    if not client_user:
        await callback.answer(_('User not found.'), show_alert=True)
        return

    async def select_group(candidates):
        former = await Chat._collection.find_one({
            "user_id": chat_user_id,
            "support_group_id": {"$in": candidates}
        })
        if former and former.get("support_group_id") in candidates:
            return former["support_group_id"]
        group_loads = {
            gid: await Chat._collection.count_documents({
                "support_group_id": gid,
                "status": "active"
            })
            for gid in candidates
        }
        if all(v == 0 for v in group_loads.values()):
            return candidates[0]
        return min(group_loads, key=group_loads.get)

    notice_text = "#muloqotda\n✅ <b>{name}</b> ({id}) \n @{username} \n mijoz qabul qilindi\n💬 Suhbat shu yerda davom etadi...\n\n".format(
        name=client_user.name,
        id=client_user.id,
        username=client_user.username or "username yo'q"
    )

    # Try candidate groups in a loop. If the bot was kicked from one, drop it and
    # try the next one — without recursing (which would re-answer the callback
    # and raise "query is too old").
    notice_sent = None
    to_group_id = None
    while group_ids and notice_sent is None:
        to_group_id = await select_group(group_ids)
        try:
            notice_sent = await callback.bot.send_message(
                chat_id=to_group_id,
                text=notice_text,
                parse_mode="HTML",
                reply_markup=EndChatKeyboard.keyboard(chatId=str(chat["_id"]))
            )
        except TelegramForbiddenError:
            # Bot was kicked from this support group — remove it and retry next.
            group_ids.remove(to_group_id)
            await User._collection.update_one(
                {"_id": user_id},
                {"$set": {"admin_groups": group_ids, "status": "admin" if group_ids else "user"}}
            )
            to_group_id = None

    if notice_sent is None:
        await callback.answer(_('No group connected to your admin account.'), show_alert=True)
        return

    # Update chat: set admin_id, support_group_id, status, claimed_at
    await Chat._collection.update_one(
        {'_id': chat['_id']},
        {'$set': {
            'admin_id': user_id,
            'support_group_id': to_group_id,
            'status': 'active',
            'claimed_at': int(datetime.now().timestamp())
        }}
    )

    await Chat._collection.update_one(
        {"_id": chat["_id"]},
        {"$set": {"notice_message_id": notice_sent.message_id}}
    )

    await MessageMap._collection.insert_one({
        "user_id": chat_user_id,
        "user_msg_id": 000,  # No specific user message here
        "group_id": str(to_group_id),
        "group_msg_id": notice_sent.message_id,
        "direction": "user_to_group",
        "created_at": int(datetime.now().timestamp())
    })

    for msg_id in chat.get("pending_message_ids", []):
        try:
            sent = await callback.bot.copy_message(
                chat_id=to_group_id,
                from_chat_id=client_user.id,
                message_id=msg_id,
                reply_to_message_id=notice_sent.message_id
            )

            await MessageMap._collection.insert_one({
                "user_id": chat_user_id,
                "user_msg_id": msg_id,
                "group_id": str(to_group_id),
                "group_msg_id": sent.message_id,
                "direction": "user_to_group",
                "created_at": int(datetime.now().timestamp())
            })

        except Exception as e:
            print(f"Failed to copy message {msg_id}: {e}")

    try:
        support_group = await callback.bot.get_chat(to_group_id)
        group_name = support_group.title or "—"
    except Exception:
        group_name = "—"

    # Update the general group message (best-effort: the claim is already applied)
    if callback.message:
        try:
            await callback.message.edit_text(
                text="#muloqotda\n✅ <b>{name}</b> ({id}) \n @{username} \n mijoz qabul qilindi\n💬 Suhbat <b>{group_name}</b>da davom etadi...".format(
                    name=client_user.name,
                    id=client_user.id,
                    username=client_user.username or "username yo'q",
                    group_name=group_name
                ),
                reply_markup=None,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Failed to update claim notification: {e}")

    await callback.answer(_('You have claimed this chat.'), show_alert=True)
