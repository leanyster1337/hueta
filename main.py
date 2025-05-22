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
PORT = int(os.getenv("PORT", 10000))

# Проверка на валидность WEBHOOK_HOST
if not WEBHOOK_HOST.startswith("https://"):
    raise ValueError("WEBHOOK_HOST должен начинаться с https:// и быть валидным URL Render-сервиса.")

WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

# Инициализация логов и бота
logging.basicConfig(level=logging.INFO)
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

# Команда /start
@dp.message(F.text.lower() == "/start")
async def cmd_start(message: types.Message):
    await message.answer("Здарова, кожаный! Пиши название фильма, если не тупой 🖕")

# Обработка текстовых сообщений
@dp.message(F.text)
async def handle_search(message: types.Message):
    query = message.text.strip()
    await message.answer("Секунду, ищу твою парашу 🎬")

    try:
        results = await search_movie(query)
        if not results:
            await message.answer("Ничего не нашёл. Может, ты и в школе так же искал знания?")
            return

        for title, magnet in results:
            await message.answer(f"<b>{title}</b>\n<code>{magnet}</code>", parse_mode=ParseMode.HTML)

    except Exception as e:
        logging.exception("Ошибка при поиске")
        await message.answer("Произошла какая-то хрень. Попробуй позже, лады?")

# Webhook-приложение
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
