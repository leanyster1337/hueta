import aiohttp
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

async def search_movie(query):
    rutracker_login = os.getenv("RUTRACKER_LOGIN")
    rutracker_password = os.getenv("RUTRACKER_PASSWORD")
    if not rutracker_login or not rutracker_password:
        raise RuntimeError("RUTRACKER_LOGIN или RUTRACKER_PASSWORD не заданы в .env")

    cookies = {}
    login_url = "https://rutracker.org/forum/login.php"
    search_url = f"https://rutracker.org/forum/tracker.php?nm={query}"

    async with aiohttp.ClientSession() as session:
        # Получаем стартовую страницу, чтобы получить cookies (SID)
        async with session.get("https://rutracker.org/forum/index.php") as resp:
            pass

        # Аутентификация: получаем cookies после логина
        async with session.post(
            login_url,
            data={
                "login_username": rutracker_login,
                "login_password": rutracker_password,
                "login": "Вход"
            },
            headers={
                "User-Agent": "Mozilla/5.0",
                "Referer": "https://rutracker.org/forum/index.php"
            }
        ) as login_resp:
            if login_resp.status != 200:
                raise RuntimeError(f"Ошибка входа на RuTracker (HTTP {login_resp.status})")
            # Получаем куки из сессии
            cookies = session.cookie_jar.filter_cookies("https://rutracker.org")
            if not cookies or "bb_session" not in cookies:
                raise RuntimeError("Не удалось получить bb_session cookie — вход не выполнен")

        # Теперь поиск
        async with session.get(search_url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Ошибка поиска на RuTracker (HTTP {resp.status})")
            html = await resp.text()

        soup = BeautifulSoup(html, "html.parser")
        results = []
        # Обычно нужные строки имеют класс tCenter hl-tr или просто hl-tr
        for row in soup.select("tr.hl-tr")[:5]:
            title_elem = row.select_one("a.tLink")
            magnet_elem = row.select_one("a.magnet-link")
            if not title_elem or not magnet_elem:
                continue
            title = title_elem.text.strip()
            magnet = magnet_elem.get("href")
            if title and magnet:
                results.append((title, magnet))

        return results
