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
from telethon import TelegramClient
import asyncio

load_dotenv()

REQUIRED_VARS = ["BOT_TOKEN", "API_ID", "API_HASH", "CHANNEL_ID", "WEBHOOK_HOST"]
missing_vars = [v for v in REQUIRED_VARS if not os.getenv(v)]
if missing_vars:
    raise RuntimeError(f"Не заданы переменные окружения: {', '.join(missing_vars)}")

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
CHANNEL_ID = os.getenv("CHANNEL_ID")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
PORT = int(os.getenv("PORT", 10000))

client = TelegramClient('bot_session', API_ID, API_HASH)

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

async def send_to_channel(file_path, title):
    entity = await client.get_entity(CHANNEL_ID)
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Файл {file_path} не найден")
    message = await client.send_file(
        entity,
        file_path,
        caption=f"🎬 {title}",
        parse_mode="html"
    )
    return message

async def is_cached(title):
    async for message in client.iter_messages(CHANNEL_ID, search=title):
        if hasattr(message, "document") and message.document:
            return message
    return None

@dp.message(F.text.lower() == "/start")
async def cmd_start(message: types.Message):
    await message.answer("Введите название фильма:")

@dp.message(F.text)
async def handle_search(message: types.Message):
    query = message.text.strip()
    await message.answer("🔍 Поиск...")

    try:
        cached = await is_cached(query)
        if cached:
            await message.answer("✅ Найден в кэше:")
            if hasattr(cached, "document") and cached.document:
                file_id = cached.id
                await bot.send_message(message.chat.id, "Файл найден в канале, пересылаю...")
                await bot.forward_message(message.chat.id, CHANNEL_ID, file_id)
            else:
                await message.answer("⚠️ Файл найден, но не удалось получить документ.")
            return

        results = await search_movie(query)
        if not results:
            await message.answer("❌ Ничего не найдено")
            return

        for title, magnet in results:
            torrent_path = f"/tmp/{title}.torrent"
            with open(torrent_path, "wb") as f:
                f.write(b"FAKE TORRENT DATA")
            msg = await send_to_channel(torrent_path, title)
            if hasattr(msg, "document") and msg.document:
                file_id = msg.id
                await bot.send_message(message.chat.id, "Файл загружен в канал, пересылаю...")
                await bot.forward_message(message.chat.id, CHANNEL_ID, file_id)
                await message.answer(f"📥 Файл сохранён в канале: {CHANNEL_ID}")
            else:
                await message.answer("⚠️ Не удалось отправить файл в канал.")
            break

    except Exception as e:
        logging.exception(e)
        await message.answer(f"⚠️ Ошибка. Попробуйте позже.\n{e}")

async def on_startup(app):
    await client.start(bot_token=BOT_TOKEN)  # <-- асинхронный запуск Telethon
    await bot.set_webhook(f"{WEBHOOK_HOST}/webhook")

def create_app():
    app = web.Application()
    SimpleRequestHandler(dp, bot).register(app, "/webhook")
    setup_application(app, dp)
    app.on_startup.append(on_startup)
    return app

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=PORT)
