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
@router.message(F.chat.type.in_({"group", "supergroup"}), ~F.text.startswith("/"))
async def admin_reply(message: Message, user_id=None):
    # May be invoked from _choose_to_send with a missing reply message.
    if message is None:
        return False

    # reply_to_message.from_user can be None (anonymous admin posts, messages
    # auto-forwarded from a linked channel). Guard before touching .is_bot.
    rtm = message.reply_to_message
    is_bot_reply = bool(rtm and rtm.from_user and rtm.from_user.is_bot)
    is_human_reply = bool(rtm and rtm.from_user and not rtm.from_user.is_bot)

    # Check if this chat is one of the admin groups
    is_admin_group = await User._collection.find_one({
    "admin_groups": {"$in": [str(message.chat.id)]}
})

    if not is_admin_group:
        return False
    if user_id:
        pass
    elif is_bot_reply:

        mapping = await MessageMap._collection.find_one({
            "group_id": str(message.chat.id),
            "group_msg_id": rtm.message_id,
            "direction": "user_to_group"
        })

        if not mapping:
            await message.reply(_(f"Cannot find the original user for this reply. {message.chat.id} {rtm.message_id}"))
            return False

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
            return False

        elif chatsCount > 1:

            users = []
            for c in chats:
                user = await User.get(c["user_id"])
                if user: users.append((c["user_id"], user.name))

            await message.reply(_("Bu chat uchun bir nechta faol suhbat topildi. \nYuborish uchun mijozni tanlang:"), reply_markup=ChooseToSend.keyboard(users))
            return False
        else:
            user_id = chats[0]["user_id"]

    if is_human_reply:

        mapping = await MessageMap._collection.find_one({
            "group_id": str(message.chat.id),
            "group_msg_id": rtm.message_id,
            "direction": "group_to_user"
        })

        if mapping:
            reply_to_msg_id = mapping["user_msg_id"]
        else:
            reply_to_msg_id = None
    else:
        reply_to_msg_id = None



    try:
        sent = await message.bot.copy_message(
            chat_id=user_id,
            from_chat_id=message.chat.id,
            message_id=message.message_id,
            reply_to_message_id=reply_to_msg_id
        )

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

        return True

    except Exception as e:
        logger.error(f"Failed to send to user {user_id}: {e}")
        return False
        
        

@router.callback_query(ChooseToSend.Callback.filter())
async def _choose_to_send(call: CallbackQuery, callback_data: ChooseToSend.Callback):
    await call.answer()

    user_id = callback_data.data
    message = call.message.reply_to_message if call.message else None

    if message is None:
        await call.answer(_("Asl xabar topilmadi."), show_alert=True)
        return

    user = await User.get(int(user_id))
    if not user:
        await call.answer(_("Foydalanuvchi topilmadi."), show_alert=True)
        return

    ok = await admin_reply(message, user_id=int(user_id))
    await call.message.edit_reply_markup(reply_markup=None)
    if ok:
        await call.message.edit_text(f"{user.name} ({user.id}) ga yuborildi.")
    else:
        await call.message.edit_text(f"{user.name} ({user.id}) ga yuborib bo'lmadi.")



