import os
import asyncio
from aiogram import types

DOWNLOAD_DIR = "./downloads"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

async def handle_download(callback: types.CallbackQuery, bot, channel_id=None):
    magnet = callback.data
    await callback.message.answer("Скачиваю фильм, подожди...")

    filename = "movie.mp4"
    filepath = os.path.join(DOWNLOAD_DIR, filename)

    # Удаление старого
    if os.path.exists(filepath):
        os.remove(filepath)

    proc = await asyncio.create_subprocess_exec(
        "aria2c", magnet, "--dir=" + DOWNLOAD_DIR, "--out=" + filename,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE
    )
    await proc.communicate()

    if os.path.exists(filepath) and os.path.getsize(filepath) < 2 * 1024 * 1024 * 1024:
        await callback.message.answer_document(types.FSInputFile(filepath), caption="Вот твой фильм!")

        if channel_id:
            await bot.send_document(channel_id, types.FSInputFile(filepath), caption="Новый фильм!")
    else:
        await callback.message.answer("Файл не найден или слишком большой для Telegram.")