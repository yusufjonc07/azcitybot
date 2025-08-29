
from fastapi import FastAPI
from loader import dp, bot
from data.config import WEBHOOK_URL
from app import setup_routes, setup_middlewares, set_default_commands
from utils import logger
from aiogram.exceptions import TelegramBadRequest

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    await setup_middlewares(dp)
    await setup_routes(dp)
    
    try:
        await bot.delete_webhook()
        await bot.set_webhook(WEBHOOK_URL)
        await set_default_commands()
    except Exception as e:
        logger.error(f"Error: {e}")
        
    logger.info("Bot started!")

@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Bot stopped!")

@app.post("/webhook")
async def webhook(update: dict):
    try:
        await dp.feed_webhook_update(bot, update)
    except TelegramBadRequest as e:
        logger.error(f"Error processing webhook update: {e}")
    except Exception as e:
        logger.error(f"Unexpected error processing webhook update: {e}")
    return {"ok": True}