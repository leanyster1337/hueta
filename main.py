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
from kinosimka_utils import get_download_links
import aiohttp

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
PORT = int(os.getenv("PORT", 10000))

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher(storage=MemoryStorage())

user_search_results = {}
user_quality_links = {}

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
    await callback.message.answer(f"Выберите качество для «{title}»:")

    # Получаем варианты качества
    links = await get_download_links(link)
    if not links:
        await callback.message.answer("⚠️ Не удалось найти ссылки для скачивания.")
        return

    user_quality_links[callback.from_user.id] = links
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=f"{l['text']} ({l['quality']})",
                callback_data=f"dl_{idx}_{i}"
            )]
            for i, l in enumerate(links)
        ]
    )
    await callback.message.answer("Доступные варианты:", reply_markup=kb)

@dp.callback_query(F.data.startswith("dl_"))
async def process_download(callback: CallbackQuery):
    _, film_idx, link_idx = callback.data.split("_")
    film_idx = int(film_idx)
    link_idx = int(link_idx)
    results = user_search_results.get(callback.from_user.id)
    if not results or film_idx >= len(results):
        await callback.answer("Некорректный выбор (фильм)")
        return
    title, link = results[film_idx]
    links = user_quality_links.get(callback.from_user.id)
    if not links or link_idx >= len(links):
        await callback.answer("Некорректный выбор (качество)")
        return
    file_url = links[link_idx]["url"]
    quality = links[link_idx]["quality"]

    fname = f"{title}_{quality}.mp4"
    await callback.message.answer(f"Скачиваю файл {fname}...")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(file_url) as resp:
                if resp.status != 200:
                    await callback.message.answer("Ошибка скачивания видео.")
                    return
                with open(fname, "wb") as f:
                    while True:
                        chunk = await resp.content.read(1024*1024)
                        if not chunk:
                            break
                        f.write(chunk)
        await callback.message.answer("Отправляю видео...")
        await bot.send_video(callback.from_user.id, types.FSInputFile(fname), caption=title)
        os.remove(fname)
    except Exception as e:
        logging.exception(e)
        await callback.message.answer(f"⚠️ Ошибка при скачивании/отправке видео: {e}")

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
