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
from telethon.tl.types import InputPeerChannel
import asyncio

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
CHANNEL_ID = os.getenv("CHANNEL_ID")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
PORT = int(os.getenv("PORT", 10000))

# Инициализация Telethon
client = TelegramClient('bot_session', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

# Инициализация aiogram
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

async def send_to_channel(file_path, title):
    entity = await client.get_entity(CHANNEL_ID)
    message = await client.send_file(
        entity,
        file_path,
        caption=f"🎬 {title}",
        parse_mode="html"
    )
    return message

async def is_cached(title):
    async for message in client.iter_messages(CHANNEL_ID, search=title):
        if message.file:
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
        # Проверка кэша
        cached = await is_cached(query)
        if cached:
            await message.answer("✅ Найден в кэше:")
            await bot.send_document(message.chat.id, cached.file.id)
            return

        # Поиск и загрузка
        results = await search_movie(query)
        if not results:
            await message.answer("❌ Ничего не найдено")
            return

        for title, magnet in results:
            # Скачивание торрента (заглушка)
            torrent_path = f"/tmp/{title}.torrent"
            
            # Отправка в канал и пользователю
            msg = await send_to_channel(torrent_path, title)
            await bot.send_document(message.chat.id, msg.file.id)
            await message.answer(f"📥 Файл сохранён в канале: {CHANNEL_ID}")

    except Exception as e:
        logging.error(f"Ошибка: {e}")
        await message.answer("⚠️ Ошибка. Попробуйте позже.")

async def on_startup(app):
    await bot.set_webhook(f"{WEBHOOK_HOST}/webhook")

def create_app():
    app = web.Application()
    SimpleRequestHandler(dp, bot).register(app, "/webhook")
    setup_application(app, dp)
    app.on_startup.append(on_startup)
    return app

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(client.start())
    app = create_app()
    web.run_app(app, host="0.0.0.0", port=PORT)
