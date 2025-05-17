import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web
import aiohttp
from bs4 import BeautifulSoup

# Конфигурация
BOT_TOKEN = "7593641535:AAELSxTmLO5pxfzNLKi1vAeS-XKsLKSmlek"
CHANNEL_ID = "@leanysterj"
RUTRACKER_LOGIN = "leanyster"
RUTRACKER_PASSWORD = "Balakakotik29"
WEBHOOK_HOST = "https://hueta.onrender.com"
WEBHOOK_PATH = "/webhook"
DOWNLOAD_DIR = "./downloads"
MAX_FILE_SIZE = 2 * 1024 * 1024 * 1024  # 2GB

# Настройка логгирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота
bot = Bot(token=BOT_TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher(storage=MemoryStorage())

# Создаем папку для загрузок
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

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
            if response.status != 200:
                logger.error(f"Ошибка авторизации: {response.status}")
                return False
            return True
    except Exception as e:
        logger.error(f"Ошибка при авторизации: {e}")
        return False

async def search_rutracker(query):
    """Поиск на Rutracker"""
    search_url = f"https://rutracker.org/forum/tracker.php?nm={query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    async with aiohttp.ClientSession(headers=headers) as session:
        if not await rutracker_login(session):
            return []
        
        try:
            async with session.get(search_url) as response:
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
                
                return results[:10]  # Ограничиваем 10 результатами
        
        except Exception as e:
            logger.error(f"Ошибка при парсинге: {e}")
            return []

async def create_search_keyboard(results):
    """Создание клавиатуры с результатами"""
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=[])
    for item in results:
        keyboard.inline_keyboard.append([
            types.InlineKeyboardButton(text=item["title"], callback_data=item["magnet"])
        ])
    return keyboard

async def download_file(magnet, filename):
    """Скачивание файла через aria2c"""
    filepath = os.path.join(DOWNLOAD_DIR, filename)
    
    # Удаляем старый файл если существует
    if os.path.exists(filepath):
        os.remove(filepath)
    
    # Запускаем скачивание
    proc = await asyncio.create_subprocess_exec(
        "aria2c", "--seed-time=0", "--max-overall-download-limit=10M",
        magnet, "--dir=" + DOWNLOAD_DIR, "--out=" + filename,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    
    await proc.communicate()
    return filepath if os.path.exists(filepath) else None

@dp.message(Command("start"))
async def cmd_start(message: types.
Message):
    """Обработчик команды /start"""
    await message.answer(
        "🎬 <b>Кинобот</b>\n\n"
        "Отправь мне название фильма или сериала, и я найду его на Rutracker!\n\n"
        "📌 <i>Бот поддерживает скачивание только файлов до 2GB</i>"
    )

@dp.message()
async def handle_search(message: types.Message):
    """Обработчик поисковых запросов"""
    query = message.text.strip()
    if not query:
        await message.answer("🔍 Введите название фильма для поиска.")
        return
    
    msg = await message.answer("🔎 Ищу на Rutracker...")
    
    try:
        results = await search_rutracker(query)
        if not results:
            await msg.edit_text("😕 Ничего не найдено. Попробуйте изменить запрос.")
            return
        
        keyboard = await create_search_keyboard(results)
        await msg.edit_text(
            f"🎥 Найдено {len(results)} результатов по запросу <b>'{query}'</b>:",
            reply_markup=keyboard
        )
    
    except Exception as e:
        logger.error(f"Search error: {e}")
        await msg.edit_text("⚠️ Произошла ошибка при поиске. Попробуйте позже.")

@dp.callback_query()
async def handle_download(callback: types.CallbackQuery):
    """Обработчик скачивания"""
    magnet = callback.data
    filename = f"movie_{callback.message.message_id}.mp4"
    
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
        msg = await callback.message.answer("⏳ Начинаю скачивание...")
        
        filepath = await download_file(magnet, filename)
        if not filepath:
            await msg.edit_text("❌ Не удалось скачать файл.")
            return
        
        file_size = os.path.getsize(filepath)
        if file_size > MAX_FILE_SIZE:
            await msg.edit_text("⚠️ Файл слишком большой для Telegram (макс. 2GB).")
            os.remove(filepath)
            return
        
        await msg.edit_text("📤 Отправляю файл...")
        await callback.message.answer_document(
            types.FSInputFile(filepath),
            caption="🎉 Вот ваш фильм!"
        )
        
        # Отправляем в канал
        await bot.send_document(
            CHANNEL_ID,
            types.FSInputFile(filepath),
            caption=f"📢 Новый фильм!\n\n🔍 Поисковый запрос: <b>{callback.message.text.split('по запросу')[1].split(':')[0].strip()}</b>"
        )
        
        await msg.delete()
        os.remove(filepath)  # Удаляем после отправки
    
    except Exception as e:
        logger.error(f"Download error: {e}")
        await callback.message.answer(f"⚠️ Ошибка: {str(e)}")

async def on_startup(app):
    """Действия при запуске"""
    await bot.set_webhook(f"{WEBHOOK_HOST}{WEBHOOK_PATH}")
    logger.info(f"Бот запущен. Webhook: {WEBHOOK_HOST}{WEBHOOK_PATH}")

async def on_shutdown(app):
    """Действия при выключении"""
    await bot.delete_webhook()
    await bot.session.close()
    logger.info("Бот остановлен")

async def create_app():
    """Создание приложения"""
    app = web.Application()
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    
    SimpleRequestHandler(dp, bot).register(app, WEBHOOK_PATH)
    setup_application(app, dp)
    
    return app

if __name__ == "__main__":
    web.run_app(create_app(), host="0.0.0.0", port=10000)
