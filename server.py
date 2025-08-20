
from fastapi import FastAPI
from loader import dp, bot
from data.config import WEBHOOK_URL

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(WEBHOOK_URL)

@app.post("/webhook")
async def webhook(update: dict):
    await dp.feed_webhook_update(bot, update)
    return {"ok": True}