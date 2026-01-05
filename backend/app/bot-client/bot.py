
import traceback
from fastapi import APIRouter
from loader import dp, bot
from app.core.config import settings
from app import setup_routes, setup_middlewares, set_default_commands
from utils import logger
from aiogram.exceptions import TelegramBadRequest

client_app = APIRouter(tags=["Client Bot Webhook"], prefix="/client-bot")

WEBHOOK_URL = f"https://{settings.DOMAIN}{client_app.prefix}/webhook"



async def notify_error(error: Exception, context: str = ""):
    """Send error notification to admin user"""
    try:
        error_message = f"🚨 <b>Error occurred</b>\n\n"
        if context:
            error_message += f"<b>Context:</b> {context}\n\n"
        error_message += f"<b>Error:</b> {type(error).__name__}\n"
        error_message += f"<b>Message:</b> {str(error)}\n\n"
        error_message += f"<b>Traceback:</b>\n<pre>{traceback.format_exc()[-3000:]}</pre>"
        await bot.send_message(settings.ERROR_NOTIFY_USER_ID, error_message, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Failed to send error notification: {e}")


@client_app.on_event("startup")
async def on_startup():
    await setup_middlewares(dp)
    await setup_routes(dp)
    
    try:
        await bot.delete_webhook()
        await bot.set_webhook(settings.WEBHOOK_URL, allowed_updates=["message", "callback_query", "edited_message", "message_reaction"])
        await set_default_commands()
    except Exception as e:
        logger.error(f"Error: {e}")
        await notify_error(e, "Bot startup - webhook setup")
        
    logger.info("Bot started!")

@client_app.on_event("shutdown")
async def on_shutdown():
    logger.info("Bot stopped!")

@client_app.post("/webhook")
async def webhook(update: dict):
    try:
        await dp.feed_webhook_update(bot, update)
    except TelegramBadRequest as e:
        logger.error(f"Error processing webhook update: {e}")
        await notify_error(e, "Webhook update - TelegramBadRequest")
    except Exception as e:
        logger.error(f"Unexpected error processing webhook update: {e}")
        await notify_error(e, "Webhook update - Unexpected error")
    return {"ok": True}