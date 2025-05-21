import aiohttp
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bs4 import BeautifulSoup

async def search_and_prepare_keyboard(query: str) -> InlineKeyboardMarkup | None:
    url = f"https://rutor.info/search/{query.replace(' ', '%20')}"
    headers = {
        "User-Agent": "Mozilla/5.0"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as response:
            html = await response.text()

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="lista2t")

    if not table:
        return None

    keyboard = InlineKeyboardMarkup(row_width=1)
    rows = table.find_all("tr")[1:6]  # максимум 5 результатов

    for row in rows:
        link_tag = row.find("a", href=True)
        if not link_tag or not link_tag["href"].startswith("/torrent/"):
            continue

        title = link_tag.text.strip()
        link = "https://rutor.info" + link_tag["href"]

        keyboard.add(InlineKeyboardButton(text=title, url=link))

    return keyboard if keyboard.inline_keyboard else None
