import aiohttp
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

async def search_movie(query):
    # Аутентификация на RuTracker
    session = aiohttp.ClientSession()
    await session.post(
        "https://rutracker.org/forum/login.php",
        data={
            "login_username": os.getenv("RUTRACKER_LOGIN"),
            "login_password": os.getenv("RUTRACKER_PASSWORD"),
            "login": "Вход"
        },
        headers={"User-Agent": "Mozilla/5.0"}
    )

    # Поиск
    url = f"https://rutracker.org/forum/tracker.php?nm={query}"
    async with session.get(url) as resp:
        html = await resp.text()
    
    soup = BeautifulSoup(html, "html.parser")
    results = []
    
    for row in soup.select("tr.tCenter.hl-tr")[:5]:
        title_elem = row.select_one("a.tLink")
        if not title_elem:
            continue
        title = title_elem.text.strip()
        magnet = row.select_one("a.magnet-link")["href"]
        results.append((title, magnet))
    
    await session.close()
    return results
