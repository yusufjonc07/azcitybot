
import asyncio
import html
import traceback
from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from loader import dp, bot
from data.config import WEBHOOK_URL
from app import setup_routes, setup_middlewares, set_default_commands
from utils import logger
from aiogram.exceptions import TelegramBadRequest

app = FastAPI()

# Company website served alongside the bot webhook.
WEB_DIR = Path(__file__).resolve().parent / "web"

# The site's HTML references assets via absolute paths (/assets/..., /static/...),
# so mount those sub-paths. We deliberately don't mount at "/" so POST /webhook
# keeps working.
app.mount("/assets", StaticFiles(directory=WEB_DIR / "assets"), name="assets")
app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")


@app.get("/")
async def home():
    """Serve the company website home page."""
    return FileResponse(WEB_DIR / "index.html")

ERROR_NOTIFY_USER_ID = 7657753017


async def notify_error(error: Exception, context: str = ""):
    """Send error notification to admin user"""
    try:
        # Escape dynamic parts so a '<' or '&' in the error/traceback doesn't
        # make Telegram reject the HTML and swallow the whole notification.
        error_message = f"🚨 <b>Error occurred</b>\n\n"
        if context:
            error_message += f"<b>Context:</b> {html.escape(context)}\n\n"
        error_message += f"<b>Error:</b> {html.escape(type(error).__name__)}\n"
        error_message += f"<b>Message:</b> {html.escape(str(error))}\n\n"
        error_message += f"<b>Traceback:</b>\n<pre>{html.escape(traceback.format_exc()[-3000:])}</pre>"
        await bot.send_message(ERROR_NOTIFY_USER_ID, error_message, parse_mode="HTML")
    except Exception as e:
        logger.error(f"Failed to send error notification: {e}")


@app.on_event("startup")
async def on_startup():
    try:
        await setup_middlewares(dp)
        await setup_routes(dp)
    except Exception as e:
        # A setup error means the bot would run with no/partial handlers — fail
        # loudly (notify + re-raise) instead of starting silently broken.
        logger.error(f"Fatal startup error (routes/middlewares): {e}")
        await notify_error(e, "Bot startup - routes/middlewares")
        raise

    # try:
    #     # await bot.delete_webhook()
    #     # await bot.set_webhook(WEBHOOK_URL, allowed_updates=["message", "callback_query", "edited_message", "message_reaction"])
    #     # await set_default_commands()
    # except Exception as e:
    #     logger.error(f"Error: {e}")
    #     await notify_error(e, "Bot startup - webhook setup")
        
    logger.info("Bot started!")

@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Bot stopped!")

@app.post("/webhook")
async def webhook(update: dict):
    asyncio.create_task(process_update(update))
    return {"ok": True}


async def process_update(update: dict):
    try:
        await dp.feed_webhook_update(bot, update)
    except TelegramBadRequest as e:
        logger.error(f"Error processing webhook update: {e}")
        await notify_error(e, "Webhook update - TelegramBadRequest")
    except Exception as e:
        logger.error(f"Unexpected error processing webhook update: {e}")
        await notify_error(e, "Webhook update - Unexpected error")