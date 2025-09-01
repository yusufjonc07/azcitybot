from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
import asyncio

TOKEN = "8420135138:AAGeBSUfzQRyj-JH13RSwPEJkpThwPjthYs"
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Start Handler
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Welcome! Please send me a message with a custom emoji.")

# This will capture any incoming message
@dp.message()
async def capture_emoji_ids(message: types.Message):
    if message.entities:
        for entity in message.entities:
            if entity.type == "custom_emoji":
                print(f"Text: {message.text[entity.offset:entity.offset+entity.length]}")
                print(f"Custom Emoji ID: {entity.custom_emoji_id}")
                # Optionally store it somewhere for later use
                await message.answer(f"Captured ID for '{message.text[entity.offset:entity.offset+entity.length]}':\n{entity.custom_emoji_id}")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
