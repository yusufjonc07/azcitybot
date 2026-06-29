import re

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, MessageEntity
from aiogram.exceptions import TelegramBadRequest
from app.keyboards.chat import ClaimChatKeyboard

from app.keyboards import LangKeyboard
from database.models import User, Chat
from database.models.messageMap import MessageMap
from loader import _

from data.config import GENERAL_CHAT_ID
from datetime import datetime
from utils import logger

router = Router()

# Strips Telegram custom (premium) emoji wrappers down to their plain fallback
# emoji, e.g. '<tg-emoji emoji-id="123">📆</tg-emoji>' -> '📆'. Used as a fallback
# when Telegram rejects a custom emoji (DOCUMENT_INVALID) so the message still sends.
_TG_EMOJI_RE = re.compile(r"<tg-emoji[^>]*>(.*?)</tg-emoji>", re.DOTALL)


def _strip_custom_emoji(text: str) -> str:
    return _TG_EMOJI_RE.sub(r"\1", text)


# /admin command handler
@router.message(Command("admin"), F.chat.type.in_({"group", "supergroup"}))
async def _admin(message: Message, user: User = None):
    # These commands live in user_router (no admin status middleware), so guard
    # explicitly — otherwise any group member could promote arbitrary admins.
    if not user or not user.is_admin():
        return
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

# /pending command handler
@router.message(Command("pending"), F.chat.type.in_({"group", "supergroup"}))
async def _pending_chats(message: Message, user: User = None):
    if not user or not user.is_admin():
        return
    if str(message.chat.id) != GENERAL_CHAT_ID:
        await message.reply(_("This command can only be used in the general chat."))
        return

    # Only chats that actually have a notification message can be re-sent.
    pending_chats = await Chat._collection.find({
        "status": "pending",
        "notificated_message_id": {"$ne": None}
    }).to_list()

    if len(pending_chats) == 0:
        await message.reply("Kutayotgan mijozlar yo'q. ✅")
        return

    for chat in pending_chats:
        notificated_message_id = chat.get("notificated_message_id")
        if not notificated_message_id:
            continue
        try:
            resent_msg = await message.bot.copy_message(
                chat_id=GENERAL_CHAT_ID,
                from_chat_id=GENERAL_CHAT_ID,
                message_id=notificated_message_id,
                reply_markup=ClaimChatKeyboard.keyboard(chat["user_id"])
            )

            ## Delete the old notificated message
            await message.bot.delete_message(
                chat_id=GENERAL_CHAT_ID,
                message_id=notificated_message_id
            )

            ## Update the chat with new notificated_message_id
            await Chat._collection.update_one(
                {"_id": chat["_id"]},
                {"$set": {"notificated_message_id": resent_msg.message_id, 'updated_at': int(datetime.now().timestamp())}}
            )
        except Exception as e:
            logger.error(f"Failed to resend pending notification for chat {chat.get('_id')}: {e}")


@router.message(Command("lang"))
async def _lang(message: Message):
    await message.answer(_("Select language:"), reply_markup=LangKeyboard.keyboard())

@router.callback_query(LangKeyboard.filter())
async def _lang_callback(call: CallbackQuery, callback_data: LangKeyboard.Callback):
    await call.answer("Processing...", show_alert=False)

    # Persist the language FIRST so the selection is saved even if the message
    # can no longer be edited (old/inaccessible message).
    try:
        await User.update(call.from_user.id, lang=callback_data.lang)
    except Exception as e:
        print(f"Error updating user language: {e}")

    if call.message:
        welcome = _("welcome_message", locale=callback_data.lang)
        try:
            await call.message.edit_text(welcome, parse_mode="HTML")
        except TelegramBadRequest as e:
            # A custom (premium) emoji with an invalid/inaccessible id makes
            # Telegram reject the whole message (DOCUMENT_INVALID). Retry with
            # the plain fallback emoji so the user still gets the welcome.
            try:
                await call.message.edit_text(_strip_custom_emoji(welcome), parse_mode="HTML")
            except Exception as e2:
                print(f"Error editing welcome message (fallback): {e2}")
        except Exception as e:
            print(f"Error editing welcome message: {e}")


# /delete command handler
@router.message(Command("delete"), F.chat.type.in_({"group", "supergroup"}))
async def _delete_message(message: Message, user: User = None):
    if not user or not user.is_admin():
        return

    if message.reply_to_message is None:
        await message.reply(_("Please reply to the message you want to delete with /delete command."))
        return
    
    message_id = message.reply_to_message.message_id
    msg_map: MessageMap | None = await MessageMap._collection.find_one({
        "group_msg_id": message_id,
        "group_id": str(message.chat.id)
    })

    if not msg_map:
        print("No message map found.", message_id, message.chat.id)
        return

    if msg_map["direction"] != "group_to_user":
        print("Message direction is not group_to_user.")
        return

    try:
        await message.bot.delete_message(
            chat_id=msg_map["user_id"],
            message_id=msg_map["user_msg_id"]
        )
        await message.bot.delete_message(
            chat_id=msg_map["group_id"],
            message_id=msg_map["group_msg_id"]
        )
        await message.bot.delete_message(
            chat_id=msg_map["group_id"],
            message_id=message.message_id
        )
        await MessageMap.delete(msg_map["_id"])
        
    except Exception as e:
        print(f"Error deleting message: {e}")
        return