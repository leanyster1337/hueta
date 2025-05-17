import os
import logging
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.types import FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiohttp import web
from bs4 import BeautifulSoup

# Логгирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Переменные среды
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")  # например: https://your-app-name.onrender.com
WEBHOOK_PATH = f"/webhook/{BOT_TOKEN}"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
PORT = int(os.getenv("PORT", 10000))

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

async def search_rutor(query: str):
    url = f"http://rutor.info/search/0/0/010/2/{query}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, "html.parser")
            rows = soup.select("tr.gai, tr.gaj")
            results = []

            for row in rows[:10]:
                link_tag = row.select_one("a[href^='/torrent/']")
                magnet_tag = row.select_one("a[href^='magnet:']")
                if not link_tag or not magnet_tag:
                    continue
                title = link_tag.text.strip()
                magnet = magnet_tag["href"]
                results.append({"title": title, "magnet": magnet})

            return results

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    await message.answer("Привет! Введи название фильма, и я найду его на Rutor.")

@dp.message()
async def handle_query(message: types.Message):
    query = message.text.strip()
    results = await search_rutor(query)
    if not results:
        await message.answer("Фильмы не найдены. Попробуйте изменить запрос.")
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=r["title"][:64], url=r["magnet"])] for r in results
    ])
    await message.answer("Найдено:", reply_markup=keyboard)

async def main():
    await bot.set_webhook(WEBHOOK_URL)
    app = web.Application()
    app.router.add_post(WEBHOOK_PATH, lambda request: dp.resolve_webhook(request, bot=bot))
    return app

if name == "__main__":
    web.run_app(main(), host="0.0.0.0", port=PORT)
