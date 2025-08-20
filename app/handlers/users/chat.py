from datetime import datetime
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message

from app.keyboards import LangKeyboard
from app.handlers.routers import user_router as router
from app.keyboards.chat import CancelChatKeyboard, ClaimChatKeyboard, NewChatKeyboard, EndChatKeyboard
from data.config import GENERAL_CHAT_ID
from database.models import Chat, User
from loader import _

@router.callback_query(NewChatKeyboard.Callback.filter())
async def _new_chat(callback: CallbackQuery, callback_data: NewChatKeyboard.Callback):
    await callback.answer("Processing your request...", show_alert=False)
    user = await User.get(callback.from_user.id)
    try:
        chat = await Chat.add(callback.from_user.id)
        print("Chat created:", chat)
        sent = await callback.bot.send_message(
            chat_id=GENERAL_CHAT_ID,
            text=f"#kutyapti Mijoz: {callback.from_user.full_name} ({callback.from_user.id})",
            reply_markup=ClaimChatKeyboard.keyboard(callback.from_user.id)
        )
        await Chat._collection.update_one({"_id": chat.id}, {"$set": {"notificated_message_id": sent.message_id}})
    except ValueError:
        chat = None
        
    except Exception as e:
        chat = None
        print(f"Error creating chat: {e}")

    await callback.message.edit_text(text=_("A support agent will reach out to you soon.", locale=user.lang))
    return 

# @router.callback_query(CancelChatKeyboard.Callback.filter())
# async def _cancel_chat(callback: CallbackQuery, callback_data: CancelChatKeyboard.Callback):
#     await callback.answer()
#     chat = await Chat._collection.find_one({
#             "user_id": callback.from_user.id,
#             "status": "pending",
#     })
    
#     if chat and chat["notificated_message_id"]:
#         await callback.bot.delete_message(GENERAL_CHAT_ID, chat["notificated_message_id"])
#         await Chat._collection.update_many({"user_id": callback.from_user.id, "status": "pending"}, {"$set": {"status": "cancelled", "cancelled_at": int(datetime.now().timestamp())}})

#     await callback.message.edit_text(text=_("Chat cancelled."), reply_markup=NewChatKeyboard.keyboard())
#     return