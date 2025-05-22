import os
import logging
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiogram.client.default import DefaultBotProperties
from search import search_movie
from kinosimka_utils import get_download_url
import aiohttp

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
PORT = int(os.getenv("PORT", 10000))

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

user_search_results = {}

@dp.message(F.text.lower() == "/start")
async def cmd_start(message: types.Message):
    await message.answer("Введите название фильма:")

@dp.message(F.text)
async def handle_search(message: types.Message):
    query = message.text.strip()
    await message.answer("🔍 Поиск...")

    try:
        results = await search_movie(query)
        if not results:
            await message.answer("❌ Ничего не найдено")
            return
        user_search_results[message.from_user.id] = results
        kb = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text=title, callback_data=f"select_{idx}")]
                for idx, (title, link) in enumerate(results)
            ]
        )
        await message.answer("Выберите нужный фильм:", reply_markup=kb)
    except Exception as e:
        logging.exception(e)
        await message.answer(f"⚠️ Ошибка. Попробуйте позже.\n{e}")

@dp.callback_query(F.data.startswith("select_"))
async def process_selection(callback: CallbackQuery):
    idx = int(callback.data.replace("select_", ""))
    results = user_search_results.get(callback.from_user.id)
    if not results or idx >= len(results):
        await callback.answer("Некорректный выбор")
        return

    title, link = results[idx]
    await callback.message.answer(f"Ищу ссылку для скачивания для «{title}»...")

    try:
        download_url = await get_download_url(link)
        if not download_url:
            await callback.message.answer("⚠️ Не удалось найти ссылку для скачивания.")
            return

        if download_url.endswith(".mp4"):
            fname = f"{title}.mp4"
            async with aiohttp.ClientSession() as session:
                async with session.get(download_url) as resp:
                    if resp.status != 200:
                        await callback.message.answer("Ошибка скачивания видео.")
                        return
                    with open(fname, "wb") as f:
                        while True:
                            chunk = await resp.content.read(1024*1024)
                            if not chunk:
                                break
                            f.write(chunk)
            await callback.message.answer("Отправляю файл...")
            await bot.send_video(callback.from_user.id, types.FSInputFile(fname), caption=title)
            os.remove(fname)
        else:
            await callback.message.answer(f"Видео найдено! Вот ссылка на скачивание или просмотр:\n{download_url}")
    except Exception as e:
        logging.exception(e)
        await callback.message.answer(f"⚠️ Ошибка при получении видео: {e}")

async def on_startup(app):
    await bot.set_webhook(f"{WEBHOOK_HOST}/webhook")

def create_app():
    from aiohttp import web
    app = web.Application()
    SimpleRequestHandler(dp, bot).register(app, "/webhook")
    setup_application(app, dp)
    app.on_startup.append(on_startup)
    return app

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    app = create_app()
    from aiohttp import web
    web.run_app(app, host="0.0.0.0", port=PORT)
