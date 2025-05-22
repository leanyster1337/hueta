import os
import logging
from dotenv import load_dotenv
from aiohttp import web
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.client.default import DefaultBotProperties
from search import search_movie

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "").strip()
CHANNEL_ID = os.getenv("CHANNEL_ID")
PORT = int(os.getenv("PORT", 10000))

if not WEBHOOK_HOST.startswith("https://"):
    raise ValueError("Invalid WEBHOOK_HOST")

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

@dp.message(F.text.lower() == "/start")
async def cmd_start(message: types.Message):
    await message.answer("Бот запущен. Введите название фильма для поиска.")

@dp.message(F.text)
async def handle_search(message: types.Message):
    query = message.text.strip()
    await message.answer("Ищем... 🔍")
    
    try:
        results = await search_movie(query)
        if not results:
            await message.answer("Ничего не найдено 😕")
            return

        # Отправка пользователю и в канал
        for title, magnet in results:
            msg = f"<b>{title}</b>\n<code>{magnet}</code>"
            await message.answer(msg, parse_mode=ParseMode.HTML)
            await bot.send_message(CHANNEL_ID, msg, parse_mode=ParseMode.HTML)

    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await message.answer("Ошибка поиска ⚠️")

async def on_startup(app: web.Application):
    await bot.set_webhook(WEBHOOK_URL)

def create_app():
    app = web.Application()
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    setup_application(app, dp)
    app.on_startup.append(on_startup)
    return app

if __name__ == "__main__":
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=PORT)
