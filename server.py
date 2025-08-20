
from fastapi import FastAPI
from loader import dp, bot

app = FastAPI()


@app.on_event("startup")
async def on_startup():
    await bot.set_webhook(config.WEBHOOK_URL)

@app.post("/webhook")
async def webhook(update: dict):
    await dp.feed_webhook_update(bot, update)
    return {"ok": True}