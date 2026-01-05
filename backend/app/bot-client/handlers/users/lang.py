from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, MessageEntity
from app.keyboards.chat import ClaimChatKeyboard

from app.keyboards import LangKeyboard
from database.models import User, Chat
from loader import _

from data.config import GENERAL_CHAT_ID
from datetime import datetime

router = Router()


# /admin command handler
@router.message(Command("admin"), F.chat.type == "group")
async def _admin(message: Message):
    if not message.chat or message.chat.type not in ("group", "supergroup"):
        await message.reply(_("This command can only be used in groups."))
        return
    # Parse username from message.text
    parts = message.text.strip().split()
    if len(parts) < 2 or not parts[1].startswith("@"):
        await message.reply(_("Usage: /admin @username"))
        return
    username = parts[1].lstrip("@")
    user = await User._collection.find_one({"username": username})
    if not user:
        await message.reply(_(f"User @{username} not found in the bot database."))
        return
    group_id = str(message.chat.id)
    admin_groups = user.get("admin_groups") or []
    if group_id not in admin_groups:
        admin_groups.append(group_id)
        await User._collection.update_one({"_id": user["_id"]}, {"$set": {"admin_groups": admin_groups, "status": "admin"}})
        await message.reply(_(f"@{username} is now an admin for this group!"))
    else:
        await message.reply(_(f"@{username} is already an admin for this group."))

# /admin command handler
@router.message(Command("pending"), F.chat.type == "group")
async def _pending_chats(message: Message):
    if str(message.chat.id) != GENERAL_CHAT_ID:
        await message.reply(_("This command can only be used in the general chat."))
        return
    
    pending_chats = await Chat._collection.find({"status": "pending"}).to_list()
    
    if len(pending_chats) == 0:
        await message.reply("Kutayotgan mijozlar yo'q. ✅")
        return
    
    for chat in pending_chats:
        resent_msg = await message.bot.copy_message(
            chat_id=GENERAL_CHAT_ID,
            from_chat_id=GENERAL_CHAT_ID,
            message_id=chat["notificated_message_id"],
            reply_markup=ClaimChatKeyboard.keyboard(chat["user_id"])
        )
        
        ## Delete the old notificated message
        await message.bot.delete_message(
            chat_id=GENERAL_CHAT_ID,
            message_id=chat["notificated_message_id"]
        )
        
        ## Update the chat with new notificated_message_id
        await Chat._collection.update_one(
            {"_id": chat["_id"]},
            {"$set": {"notificated_message_id": resent_msg.message_id, 'updated_at': int(datetime.now().timestamp())}}
        )


@router.message(Command("lang"))
async def _lang(message: Message):
    await message.answer(_("Select language:"), reply_markup=LangKeyboard.keyboard())

@router.callback_query(LangKeyboard.filter())
async def _lang_callback(call: CallbackQuery, callback_data: LangKeyboard.Callback):
    await call.answer("Processing...", show_alert=False)
    
            
    await call.message.edit_text(
        _("welcome_message", locale=callback_data.lang), parse_mode="HTML",
    )

    try:
        await User.update(call.from_user.id, lang=callback_data.lang)
    except Exception as e:
        print(f"Error updating user language: {e}")

