from aiogram import Router
from aiogram.types import CallbackQuery
from app.keyboards.chat import ClaimChatKeyboard, EndChatKeyboard
from database.models import Chat, User
from loader import _
from database.models.messageMap import MessageMap
from datetime import datetime
from aiogram.exceptions import TelegramForbiddenError
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
    # Find the admin's group (assuming admin_groups is stored in admin model, else adjust accordingly)
    # For this example, let's assume admin.admin_groups exists
    group_ids = getattr(admin, 'admin_groups', None)
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



    client_former_group = await Chat._collection.find_one({
    "user_id": chat_user_id,
    "support_group_id": {"$in": group_ids}
})

    if client_former_group and client_former_group.get("support_group_id"):
        to_group_id = client_former_group["support_group_id"]
    else:
        group_loads = {
            gid: await Chat._collection.count_documents({
                "support_group_id": gid,
                "status": "active"
            })
            for gid in group_ids
        }

        if all(v == 0 for v in group_loads.values()):
            to_group_id = group_ids[0]
        else:
            to_group_id = min(group_loads, key=group_loads.get)
   
    
    client_user = await User.get(chat_user_id)

    try:
        # Notify the group
        notice_sent = await callback.bot.send_message(
        chat_id=to_group_id,
        text="#muloqotda\n✅ <b>{name}</b> ({id}) \n @{username} \n mijoz qabul qilindi\n💬 Suhbat shu yerda davom etadi...\n\n".format(
            name=client_user.name,
        id=client_user.id,
        username=client_user.username or "username yo'q"
        ),
        parse_mode="HTML",
        reply_markup=EndChatKeyboard.keyboard(chatId=str(chat["_id"])))
    except TelegramForbiddenError:
        admin_groups = group_ids.remove(to_group_id)
        # Update admin's admin_groups
        await User._collection.update_one({"_id": user_id}, {"$set": {"admin_groups": admin_groups, "status": "admin" if admin_groups else "user"}})
        # Retry claim process
        _claim(callback, callback_data)
        return
    
    # Update chat: set admin_id, support_group_id, status, claimed_at
    await Chat._collection.update_one(
        {'_id': chat['_id']},
        {'$set': {
            'admin_id': user_id,
            'support_group_id': to_group_id,
            'status': 'active',
            'claimed_at': int(callback.message.date.timestamp())
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
    
    

    support_group = await callback.bot.get_chat(to_group_id)

    # Optionally, update the general group message
    await callback.message.edit_text( text="#muloqotda\n✅ <b>{name}</b> ({id}) \n @{username} \n mijoz qabul qilindi\n💬 Suhbat <b>{group_name}</b>da davom etadi...".format(
            name=client_user.name,
        id=client_user.id,
        username=client_user.username or "username yo'q",
        group_name=support_group.title
        ), reply_markup=None, parse_mode="HTML")
    await callback.answer(_('You have claimed this chat.'), show_alert=True)
