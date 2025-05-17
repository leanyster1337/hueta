import os
import logging
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from bs4 import BeautifulSoup
from aiohttp import web
import subprocess

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")  # https://your-render-url.onrender.com
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

CHANNEL_ID = os.getenv("CHANNEL_ID")  # Например, "@your_channel"
PORT = int(os.getenv("PORT", default=10000))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

RUTOR_URL = "https://rutor.info/search/0/0/010/2/{}"

async def search_rutor(query: str):
    async with aiohttp.ClientSession() as session:
        url = RUTOR_URL.format(query.replace(" ", "%20"))
        async with session.get(url) as response:
            html = await response.text()
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.select("tr.gai, tr.gaj")

    results = []
    for row in rows[:10]:
        link = row.select_one("a[href^='/torrent']")
        if not link:
            continue
        title = link.text.strip()
        href = link['href']
        torrent_page_url = f"https://rutor.info{href}"

        # Переход на страницу торрента и вытаскивание magnet-ссылки
        async with aiohttp.ClientSession() as session:
            async with session.get(torrent_page_url) as torrent_page:
                page_html = await torrent_page.text()
        page_soup = BeautifulSoup(page_html, "html.parser")
        magnet_tag = page_soup.find("a", href=True, string="Magnet")
        if not magnet_tag:
            continue

        magnet = magnet_tag["href"]
        results.append({
            "title": title,
            "magnet": magnet
        })

    return results

@dp.message()
async def handle_message(message: types.Message):
    results = await search_rutor(message.text)

    if not results:
        await message.answer("Фильмы не найдены, попробуй изменить запрос.")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=r["title"], callback_data=r["magnet"])]
        for r in results
    ])
    await message.answer("Выбери фильм:", reply_markup=keyboard)

@dp.callback_query()
async def handle_callback(callback: types.CallbackQuery):
    magnet = callback.data
    await callback.message.answer("Скачиваю фильм, подожди...")

    filename = "movie.mp4"
    filepath = os.path.join("downloads", filename)
    os.makedirs("downloads", exist_ok=True)

    proc = await asyncio.create_subprocess_exec(
        "aria2c", magnet, "--dir=downloads", "--out=" + filename,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await proc.communicate()

    if os.path.exists(filepath) and os.path.getsize(filepath) < 2 * 1024 * 1024 * 1024:
        await callback.message.answer_document(types.FSInputFile(filepath), caption="Готово!")
        if CHANNEL_ID:
            await bot.send_document(CHANNEL_ID, types.FSInputFile(filepath), caption="Фильм загружен")
    else:
        await callback.message.answer("Файл не удалось отправить. Возможно, он превышает 2 ГБ.")

async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)

async def main():
    app = web.Application()
    dp.startup.register(on_startup)
    dp.include_router(dp.message.router)
    setup_application(app, dp, bot=bot)
    SimpleRequestHandler(dispatcher=dp, bot=bot).register(app, path=WEBHOOK_PATH)
    return app

if name == "__main__":
    web.run_app(main(), host="0.0.0.0", port=PORT)
