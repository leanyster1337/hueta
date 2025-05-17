import os
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bs4 import BeautifulSoup
import logging

BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
RTR_LOGIN = os.getenv("RTR_LOGIN")
RTR_PASSWORD = os.getenv("RTR_PASSWORD")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s:%(message)s")
logger = logging.getLogger(__name__)

BASE_URL = "https://rutracker.org"
SEARCH_URL = BASE_URL + "/forum/tracker.php?nm={}"

headers = {
    "User-Agent": "Mozilla/5.0"
}

async def search_rutracker(query):
    login_url = f"{BASE_URL}/forum/login.php"
    payload = {
        "login_username": RTR_LOGIN,
        "login_password": RTR_PASSWORD,
        "login": "%C2%F5%EE%E4"  # кнопка "Вход"
    }

    async with aiohttp.ClientSession(headers=headers) as session:
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

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Привет! Введи название фильма, и я найду его для тебя.")

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

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except Exception as e:
        logger.error(f"Ошибка при запуске: {e}")
