from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from database.models import Chat, User
from database.models.messageMap import MessageMap
from loader import _
from aiogram.filters import Filter, Command
from aiogram.types import Message, ChatMemberUpdated
from app.keyboards.chat import ChooseToSend

import re
from utils import logger

router = Router()

class IsReply(Filter):
    async def __call__(self, message: Message) -> bool:
        return message.reply_to_message != None
    
    


# --- ADMIN REPLY HANDLER (text + media) ---
@router.message(F.chat.type == "group", ~F.text.startswith("/"))
async def admin_reply(message: Message, user_id=None):
    # Check if this chat is one of the admin groups
    is_admin_group = await User._collection.find_one({
    "admin_groups": {"$in": [str(message.chat.id)]}
})

    if not is_admin_group:
        return 
    if user_id:
        pass
    elif message.reply_to_message != None:
    
        mapping = await MessageMap._collection.find_one({
            "group_id": str(message.chat.id),
            "group_msg_id": message.reply_to_message.message_id,
            "direction": "user_to_group"
        })
        
        if not mapping:
            await message.reply(_(f"Cannot find the original user for this reply. {message.chat.id} {message.reply_to_message.message_id}"))
            return

        user_id = mapping["user_id"]
    else:
        
        chats = await Chat._collection.find({
            "support_group_id": str(message.chat.id),
            "status": "active"
        }).to_list()
        
        chatsCount = await Chat._collection.count_documents({
            "support_group_id": str(message.chat.id),
            "status": "active"
        })
        
        
        if chatsCount == 0:
            print(chatsCount)
            await message.reply(_("Bu chat uchun faol suhbat topilmadi."))
            return
        
        elif chatsCount > 1:
            
            users = []
            for c in chats:
                user = await User.get(c["user_id"])
                if user: users.append((c["user_id"], user.name))
            
            await message.reply(_("Bu chat uchun bir nechta faol suhbat topildi. \nYuborish uchun mijozni tanlang:"), reply_markup=ChooseToSend.keyboard(users))
            return
        else:
            user_id = chats[0]["user_id"]


    try:
        sent = await message.bot.copy_message(chat_id=user_id, from_chat_id=message.chat.id, message_id=message.message_id)

        # Store message mapping for edit support (admin->user)
        if sent:
            await MessageMap._collection.insert_one({
                "user_id": user_id,
                "user_msg_id": sent.message_id,
                "group_id": str(message.chat.id),
                "group_msg_id": message.message_id,
                "direction": "group_to_user",
                "created_at": int(message.date.timestamp())
            })

    except Exception as e:
        logger.error(f"Failed to send to user {user_id}: {e}")
        
        

@router.callback_query(ChooseToSend.Callback.filter())
async def _choose_to_send(call: CallbackQuery, callback_data: ChooseToSend.Callback):
    await call.answer()

    user_id = callback_data.data
    message = call.message.reply_to_message
    
    user = await User.get(int(user_id))
    if not user:
        await call.answer(_("Foydalanuvchi topilmadi."), show_alert=True)
        return
    
    await admin_reply(message, user_id=int(user_id))
    await call.message.edit_reply_markup(reply_markup=None)
    await call.message.edit_text(f"{user.name} ({user.id}) ga yuborildi.")



