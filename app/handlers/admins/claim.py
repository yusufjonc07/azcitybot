from aiogram.types import CallbackQuery
from app.handlers.routers import admin_router as router
from app.keyboards.chat import ClaimChatKeyboard, EndChatKeyboard
from database.models import Chat, User
from loader import _

@router.callback_query(ClaimChatKeyboard.Callback.filter())
async def claim_chat(callback: CallbackQuery, callback_data: ClaimChatKeyboard.Callback):
    
    print("came")
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


    client_former_group = await Chat._collection.find_one({
        'user_id': user_id,
        'support_group_id': {'$in': group_ids}
    })

    if client_former_group:
        to_group_id = client_former_group['support_group_id']
    else:
        # Count how many active clients each group has
        group_loads = {}
        for gid in group_ids:
            count = await Chat._collection.count_documents({
                'support_group_id': gid,
                'status': 'active'
            })
            group_loads[gid] = count

        if all(v == 0 for v in group_loads.values()):
            # if absolutely no active chats in any group -> default to first group
            to_group_id = group_ids[0]
        else:
            # Pick the group with the least active clients
            to_group_id = min(group_loads, key=group_loads.get)

    # Find the pending chat
    chat = await Chat._collection.find_one({
        'user_id': chat_user_id,
        'status': 'pending',
        'notificated_message_id': {'$ne': None}
    })
    if not chat:
        await callback.answer(_('Chat not found or already claimed.'), show_alert=True)
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
    
    client_user = await User.get(chat_user_id)
    
    

    # Notify the group
    sent = await callback.bot.send_message(
        chat_id=to_group_id,
        text="#muloqotda\n✅ {name} ({id}) mijoz qabul qilindi\n💬 Suhbat shu yerda davom etadi...".format(
            name=client_user.name,
        id=client_user.id
        ),
        reply_markup=EndChatKeyboard.keyboard(chatId=str(chat["_id"])))
    
    await Chat._collection.update_one(
        {"_id": chat["_id"]},
        {"$set": {"last_message_id": sent.message_id}}
    )

    support_group = await callback.bot.get_chat(to_group_id)

    # Optionally, update the general group message
    await callback.message.edit_text( text="#muloqotda\n✅ {name} ({id}) mijoz qabul qilindi\n💬 Suhbat {group_name}da davom etadi...".format(
            name=client_user.name,
        id=client_user.id,
        group_name=support_group.title
        ), reply_markup=None)
    await callback.answer(_('You have claimed this chat.'), show_alert=True)
