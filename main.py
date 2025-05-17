import os
import asyncio
import logging

from aiogram import Bot, Dispatcher, types, F
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiohttp import web

from search import search_and_prepare_keyboard
from download import handle_download

# Настройки
TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_HOST = os.getenv("WEBHOOK_HOST")  # например: https://your-bot.onrender.com
WEBHOOK_PATH = "/webhook"
WEBHOOK_URL = f"{WEBHOOK_HOST}{WEBHOOK_PATH}"
CHANNEL_ID = os.getenv("CHANNEL_ID")

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

# Логгирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dp.message(F.text)
async def handle_message(message: Message):
    try:
        results = await search_and_prepare_keyboard(message.text)
        if results:
            await message.answer("Выберите фильм:", reply_markup=results)
        else:
            await message.answer("Фильмы не найдены. Попробуйте изменить запрос.")
    except Exception as e:
        logger.exception("Ошибка при поиске фильма")
        await message.answer("Произошла ошибка при поиске фильма.")


@dp.callback_query()
async def callback_handler(callback: types.CallbackQuery):
    try:
        await handle_download(callback, bot, CHANNEL_ID)
    except Exception as e:
        logger.exception("Ошибка при скачивании фильма")
        await callback.message.answer("Ошибка при скачивании фильма.")


async def main():
    app = web.Application()
    app.router.add_post(WEBHOOK_PATH, dp.webhook_handler(bot))
    await bot.set_webhook(WEBHOOK_URL)
    return app


if name == "__main__":
    web.run_app(main(), host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
