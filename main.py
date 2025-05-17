import os
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import aiohttp
from bs4 import BeautifulSoup
import cfscrape

# Конфигурация
BOT_TOKEN = "7593641535:AAELSxTmLO5pxfzNLKi1vAeS-XKsLKSmlek"
CHANNEL_ID = "@leanysterj"
RUTRACKER_LOGIN = "leanyster"
RUTRACKER_PASSWORD = "Balakakotik29"
WEBHOOK_HOST = "https://hueta.onrender.com"
WEBHOOK_PATH = "/webhook"

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

async def create_scraper():
    """Создание сессии с обходом Cloudflare"""
    return cfscrape.create_scraper()

async def rutracker_login(session):
    """Авторизация на Rutracker"""
    login_url = "https://rutracker.org/forum/login.php"
    data = {
        "login_username": RUTRACKER_LOGIN,
        "login_password": RUTRACKER_PASSWORD,
        "login": "Вход"
    }
    try:
        async with session.post(login_url, data=data) as response:
            return response.status == 200
    except Exception as e:
        logger.error(f"Ошибка авторизации: {e}")
        return False

async def search_rutracker(query):
    """Поиск на Rutracker с обходом защиты"""
    search_url = f"https://rutracker.org/forum/tracker.php?nm={query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "https://rutracker.org/forum/index.php"
    }
    
    try:
        scraper = await create_scraper()
        session = scraper.session
        
        if not await rutracker_login(session):
            return []
        
        async with session.get(search_url, headers=headers) as response:
            if response.status != 200:
                logger.error(f"Ошибка поиска: {response.status}")
                return []
            
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            results = []
            
            for row in soup.select('tr.tCenter.hl-tr'):
                title_elem = row.select_one('td.t-title a.tLink')
                magnet_elem = row.select_one('a.magnet-link')
                
                if title_elem and magnet_elem:
                    title = title_elem.text.strip()
                    magnet = magnet_elem['href']
                    results.append({"title": title, "magnet": magnet})
            
            return results[:5]  # Ограничиваем 5 результатами
    
    except Exception as e:
        logger.error(f"Ошибка поиска: {e}")
        return []

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("🔍 Привет! Отправь мне название фильма для поиска на Rutracker")

@dp.message()
async def handle_search(message: types.Message):
    query = message.text.strip()
    if not query:
        return await message.answer("Введите название фильма")
    
    msg = await message.answer("🔎 Ищу на Rutracker...")
    
    try:
        results = await search_rutracker(query)
        if not results:
            return await msg.edit_text("😕 Ничего не найдено")
        
        keyboard = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text=r["title"], callback_data=r["magnet"])]
            for r in results
        ])
        await msg.edit_text(f"🎬 Найдено {len(results)} вариантов:", reply_markup=keyboard)
    
    except Exception as e:
        await msg.edit_text("⚠️ Ошибка поиска. Попробуйте позже")

@dp.callback_query()
async def handle_magnet(callback: types.CallbackQuery):
    magnet = callback.data
    await callback.message.edit_reply_markup()
    await callback.message.answer(f"🔗 Магнет-ссылка:\n<code>{magnet}</code>\n\n"
"Скопируйте её в ваш torrent-клиент для скачивания")

async def on_startup(app):
    await bot.set_webhook(f"{WEBHOOK_HOST}{WEBHOOK_PATH}")

app = web.Application()
app.router.add_post("/webhook", SimpleRequestHandler(dp, bot).handle)
app.on_startup.append(on_startup)

if __name__ == "__main__":
    web.run_app(app, host="0.0.0.0", port=10000)
