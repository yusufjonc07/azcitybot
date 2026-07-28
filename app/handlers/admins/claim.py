import asyncio
from datetime import datetime

from aiogram import Router
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import CallbackQuery

from app.keyboards.chat import ClaimChatKeyboard, EndChatKeyboard
from database.models import Chat, User
from database.models.messageMap import MessageMap
from loader import _
from utils import logger

router = Router()


async def _select_support_group(user_id: int, candidates: list[int]) -> int:
    """
    Reuse the user's previous support group if possible.
    Otherwise, choose the least-loaded active support group.
    """
    former = await Chat._collection.find_one(
        {
            "user_id": user_id,
            "support_group_id": {"$in": candidates},
        }
    )

    if former:
        group_id = former.get("support_group_id")
        if group_id in candidates:
            return group_id

    loads = {}
    for group_id in candidates:
        loads[group_id] = await Chat._collection.count_documents(
            {
                "support_group_id": group_id,
                "status": "active",
            }
        )

    return min(loads, key=loads.get)


async def _send_notice(callback: CallbackQuery, chat, admin_id: int, groups: list[int], client):
    """
    Try sending the conversation notice to one of the admin's groups.
    Automatically removes groups where the bot was kicked.
    """
    notice_text = (
        "#muloqotda\n"
        f"✅ <b>{client.name}</b> ({client.id})\n"
        f"@{client.username or 'username yo\'q'}\n"
        "mijoz qabul qilindi\n"
        "💬 Suhbat shu yerda davom etadi..."
    )

    available = groups.copy()

    while available:
        group_id = await _select_support_group(client.id, available)

        try:
            message = await callback.bot.send_message(
                chat_id=group_id,
                text=notice_text,
                parse_mode="HTML",
                reply_markup=EndChatKeyboard.keyboard(chatId=str(chat["_id"])),
            )
            return group_id, message

        except TelegramForbiddenError:
            logger.warning("Bot removed from support group %s", group_id)

            available.remove(group_id)

            await User._collection.update_one(
                {"_id": admin_id},
                {
                    "$set": {
                        "admin_groups": available,
                        "status": "admin" if available else "user",
                    }
                },
            )

    return None, None


async def _finish_claim(
    callback: CallbackQuery,
    callback_message,
    chat,
    client,
    group_id: int,
    notice,
):
    """
    Runs in the background, after the webhook has already returned.
    Copies any pending messages into the support group and updates
    the claim notification with the final group name.
    """
    for user_message_id in chat.get("pending_message_ids", []):
        try:
            copied = await callback.bot.copy_message(
                chat_id=group_id,
                from_chat_id=client.id,
                message_id=user_message_id,
                reply_to_message_id=notice.message_id,
            )

            await MessageMap._collection.insert_one(
                {
                    "user_id": client.id,
                    "user_msg_id": user_message_id,
                    "group_id": str(group_id),
                    "group_msg_id": copied.message_id,
                    "direction": "user_to_group",
                    "created_at": int(datetime.now().timestamp()),
                }
            )

        except Exception:
            logger.exception(
                "Failed to copy message %s for user %s",
                user_message_id,
                client.id,
            )

    try:
        support_group = await callback.bot.get_chat(group_id)
        group_name = support_group.title or "—"
    except Exception:
        group_name = "—"

    if callback_message:
        try:
            await callback_message.edit_text(
                (
                    "#muloqotda\n"
                    f"✅ <b>{client.name}</b> ({client.id})\n"
                    f"@{client.username or 'username yo\'q'}\n"
                    "mijoz qabul qilindi\n"
                    f"💬 Suhbat <b>{group_name}</b>da davom etadi..."
                ),
                parse_mode="HTML",
                reply_markup=None,
            )

        except Exception:
            logger.exception("Failed to edit claim notification message.")


@router.callback_query(ClaimChatKeyboard.Callback.filter())
async def claim_chat(
    callback: CallbackQuery,
    callback_data: ClaimChatKeyboard.Callback,
):
    print("Answering...")
    # Acknowledge immediately to avoid callback expiration.
    await callback.answer()

    print("Finding admin and client...")
    admin_id = callback.from_user.id
    client_id = int(callback_data.data)

    admin = await User.get(admin_id)

    if not admin:
        print("Admin not found:", admin_id)
        return

    group_ids = list(getattr(admin, "admin_groups", []) or [])

    if not group_ids:
        print("Admin has no support groups:", admin_id)
        return

    # Atomically claim the chat so two admins can't both grab it.
    chat = await Chat._collection.find_one_and_update(
        {
            "user_id": client_id,
            "status": "pending",
            "notificated_message_id": {"$ne": None},
        },
        {
            "$set": {
                "status": "claiming",
                "admin_id": admin_id,
            }
        },
        return_document=True,
    )

    if not chat:
        print("Chat not found or already claimed:", client_id)
        return

    client = await User.get(client_id)

    if not client:
        print("Client not found:", client_id)
        # Revert so the chat doesn't get stuck in "claiming".
        await Chat._collection.update_one(
            {"_id": chat["_id"]},
            {"$set": {"status": "pending"}},
        )
        return

    group_id, notice = await _send_notice(
        callback,
        chat,
        admin_id,
        group_ids,
        client,
    )

    if notice is None:
        logger.warning(
            "Admin %s has no valid support groups.",
            admin_id,
        )
        # Revert so the chat doesn't get stuck in "claiming".
        await Chat._collection.update_one(
            {"_id": chat["_id"]},
            {"$set": {"status": "pending"}},
        )
        return

    now = int(datetime.now().timestamp())

    await Chat._collection.update_one(
        {"_id": chat["_id"]},
        {
            "$set": {
                "support_group_id": group_id,
                "status": "active",
                "claimed_at": now,
                "notice_message_id": notice.message_id,
            }
        },
    )

    await MessageMap._collection.insert_one(
        {
            "user_id": client_id,
            "user_msg_id": 0,
            "group_id": str(group_id),
            "group_msg_id": notice.message_id,
            "direction": "user_to_group",
            "created_at": now,
        }
    )

    # Copying pending messages + editing the notice can be slow if there
    # are many of them, so do it in the background and let the webhook
    # return right away.
    asyncio.create_task(
        _finish_claim(
            callback=callback,
            callback_message=callback.message,
            chat=chat,
            client=client,
            group_id=group_id,
            notice=notice,
        )
    )
    
    return