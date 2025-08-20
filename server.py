
from fastapi import FastAPI
from loader import dp, bot
from data.config import WEBHOOK_URL
from app import setup_routes, setup_middlewares, set_default_commands
from utils import logger

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    await setup_middlewares(dp)
    await setup_routes(dp)
    # await set_default_commands()
    await bot.delete_webhook()
    await bot.set_webhook(WEBHOOK_URL)
    logger.info("Bot started!")

@app.on_event("shutdown")
async def on_shutdown():
    logger.info("Bot stopped!")

@app.post("/webhook")
async def webhook(update: dict):
    await dp.feed_webhook_update(bot, update)
    return {"ok": True}