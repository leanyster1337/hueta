import os
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
from bs4 import BeautifulSoup
import logging

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")
WEBHOOK_PATH = f"/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"

RTR_LOGIN = os.getenv("RTR_LOGIN")
RTR_PASSWORD = os.getenv("RTR_PASSWORD")
CHANNEL_ID = os.getenv("CHANNEL_ID")

BASE_URL = "https://rutracker.org"
SEARCH_URL = BASE_URL + "/forum/tracker.php?nm={}"
HEADERS = {"User-Agent": "Mozilla/5.0"}

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

async def search_rutracker(query):
    login_url = f"{BASE_URL}/forum/login.php"
    payload = {
        "login_username": RTR_LOGIN,
        "login_password": RTR_PASSWORD,
        "login": "%C2%F5%EE%E4"
    }

    async with aiohttp.ClientSession(headers=HEADERS) as session:
        try:
            async with session.post(login_url, data=payload) as login_resp:
                if login_resp.status != 200:
                    logger.error("Ошибка авторизации на Rutracker")
                    return []

            async with session.get(SEARCH_URL.format(query)) as resp:
                html = await resp.text()
                soup = BeautifulSoup(html, "html.parser")
                topics = soup.select("a.tLink")
                results = []
                for link in topics[:10]:
                    title = link.text.strip()
                    href = BASE_URL + link["href"]
                    results.append({"title": title, "href": href})
                return results
        except Exception as e:
            logger.error(f"Ошибка при поиске: {e}")
            return []

@dp.message()
async def handle_query(message: types.Message):
    query = message.text.strip()
    await message.answer("Ищу...")
    results = await search_rutracker(query)
    if not results:
        await message.answer("Фильмы не найдены. Попробуйте изменить запрос.")
        return
    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text=r["title"], url=r["href"])] for r in results]
    )
    await message.answer("Выбери фильм:", reply_markup=keyboard)

async def on_startup(bot: Bot):
    await bot.set_webhook(WEBHOOK_URL)

async def main():
    app = web.Application()
    dp.include_router(dp.message.router)
    webhook_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_handler.register(app, path=WEBHOOK_PATH)
    setup_application(app, dp, bot=bot)

    await on_startup(bot)
    return app

if __name__ == "__main__":
    web.run_app(main(), host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
