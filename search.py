import aiohttp
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

async def search_movie(query):
    # Аутентификация на RuTracker
    login_url = "https://rutracker.org/forum/login.php"
    session = aiohttp.ClientSession()
    
    # Логин
    await session.post(login_url, data={
        "login_username": os.getenv("RUTRACKER_LOGIN"),
        "login_password": os.getenv("RUTRACKER_PASSWORD"),
        "login": "Вход"
    }, headers={"User-Agent": "Mozilla/5.0"})
    
    # Поиск
    url = f"https://rutracker.org/forum/tracker.php?nm={query.replace(' ', '+')}"
    async with session.get(url) as resp:
        html = await resp.text()
    
    soup = BeautifulSoup(html, "html.parser")
    results = []
    
    # Парсинг результатов
    for row in soup.select("tr.tCenter.hl-tr")[:5]:
        title_elem = row.select_one("a.tLink")
        if not title_elem:
            continue
            
        title = title_elem.text.strip()
        torrent_url = "https://rutracker.org/forum/" + title_elem["href"]
        
        # Получение magnet-ссылки
        async with session.get(torrent_url) as page:
            page_html = await page.text()
            page_soup = BeautifulSoup(page_html, "html.parser")
            magnet = page_soup.find("a", {"class": "magnet-link"})
            if magnet:
                results.append((title, magnet["href"]))
    
    await session.close()
    return results
