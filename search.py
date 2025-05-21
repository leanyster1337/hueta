import requests
from bs4 import BeautifulSoup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

async def search_and_prepare_keyboard(query: str):
    url = f"https://rutor.info/search/0/0/000/0/{query}"
    response = requests.get(url, timeout=10)
    soup = BeautifulSoup(response.text, "html.parser")
    rows = soup.select("tr.gai")

    if not rows:
        return None, []

    keyboard = InlineKeyboardMarkup(inline_keyboard=[])
    results = []

    for row in rows[:5]:
        title = row.select_one("a[href*='torrent']")
        if title:
            text = title.text.strip()
            link = "https://rutor.info" + title.get("href")
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text=text[:64], url=link)
            ])
            results.append((text, link))

    return keyboard, results
