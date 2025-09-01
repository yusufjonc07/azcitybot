from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message, MessageEntity

from app.keyboards import LangKeyboard
from database.models import User
from loader import _

router = Router()


# /admin command handler
@router.message(Command("admin"))
async def _admin(message: Message):
    print("Received /admin command")
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
    admin_groups = user.get("admin_groups", [])
    if group_id not in admin_groups:
        admin_groups.append(group_id)
        await User._collection.update_one({"_id": user["_id"]}, {"$set": {"admin_groups": admin_groups, "status": "admin"}})
        await message.reply(_(f"@{username} is now an admin for this group!"))
    else:
        await message.reply(_(f"@{username} is already an admin for this group."))


@router.message(Command("lang"))
async def _lang(message: Message):
    await message.answer(_("Select language:"), reply_markup=LangKeyboard.keyboard())

@router.callback_query(LangKeyboard.filter())
async def _lang_callback(call: CallbackQuery, callback_data: LangKeyboard.Callback):
    await call.answer("Processing...", show_alert=False)
    
    welcome_message = _("welcome_message", locale=callback_data.lang)
    
    emoji_map = {
        "🙂": "5371073319107827779",
        "✈️": "5361600266225326825",
        "📍": "5391032818111363540",
        "📆": "5431897022456145283",
        "✍️": "5458382591121964689",
        "👨‍💻": "5190498849440931467"
    }
    
    entities = []
    for emoji_char, emoji_id in emoji_map.items():
        start = 0
        while True:
            idx = welcome_message.find(emoji_char, start)
            if idx == -1:
                break
            entities.append(MessageEntity(
                type="custom_emoji",
                offset=idx,
                length=len(emoji_char),
                custom_emoji_id=emoji_id
            ))
            start = idx + len(emoji_char)
            
    await call.message.edit_text(
        welcome_message, entities=entities
    )

    try:
        await User.update(call.from_user.id, lang=callback_data.lang)
    except Exception as e:
        print(f"Error updating user language: {e}")

