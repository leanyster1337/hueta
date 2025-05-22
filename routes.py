from aiohttp import web
from aiogram import Dispatcher, types
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from search import search_movie

def setup_routes(app):
    dp: Dispatcher = app["dp"]

    @dp.message()
    async def handle_message(message: types.Message):
        query = message.text.strip()
        results = search_movie(query)
        if not results:
            await message.answer("Фильмы не найдены.")
        else:
            for magnet in results:
                await message.answer(magnet)

    SimpleRequestHandler(dispatcher=dp, bot=app["bot"]).register(app, path="/webhook")
    setup_application(app, dp)