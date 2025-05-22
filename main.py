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

# Загрузка .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST", "").strip()
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
PORT = int(os.getenv("PORT", 10000))

# Настройка логов
logging.basicConfig(level=logging.INFO)

# Инициализация бота
bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher(storage=MemoryStorage())

# Стартовое сообщение
@dp.message(F.text.lower() == "/start")
async def start_cmd(message: types.Message):
    await message.answer("Здарова, кожаный! Пиши название фильма, если не тупой 🖕")

# Обработка текстовых сообщений — поиск фильма
@dp.message(F.text)
async def handle_search(message: types.Message):
    query = message.text.strip()
    await message.answer("Секунду, ищу твою парашу 🎬")

    try:
        results = await search_movie(query)
        if not results:
            await message.answer("Ничего не нашёл. Может, ты и в школе также искал знания?")
            return

        for title, magnet in results:
            await message.answer(f"<b>{title}</b>\n<code>{magnet}</code>", parse_mode=ParseMode.HTML)

    except Exception as e:
        logging.exception("Ошибка при поиске")
        await message.answer("Произошла какая-то хрень. Попробуй позже, лады?")

# Запуск aiohttp-приложения
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
