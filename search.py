import aiohttp
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

async def search_movie(query):
    # Проверяем наличие логина и пароля RuTracker
    rutracker_login = os.getenv("RUTRACKER_LOGIN")
    rutracker_password = os.getenv("RUTRACKER_PASSWORD")
    if not rutracker_login or not rutracker_password:
        raise RuntimeError("RUTRACKER_LOGIN или RUTRACKER_PASSWORD не заданы в .env")

    session = aiohttp.ClientSession()
    try:
        # Аутентификация на RuTracker
        async with session.post(
            "https://rutracker.org/forum/login.php",
            data={
                "login_username": rutracker_login,
                "login_password": rutracker_password,
                "login": "Вход"
            },
            headers={"User-Agent": "Mozilla/5.0"}
        ) as login_resp:
            if login_resp.status != 200:
                raise RuntimeError("Ошибка входа на RuTracker (HTTP {})".format(login_resp.status))

        # Поиск
        url = f"https://rutracker.org/forum/tracker.php?nm={query}"
        async with session.get(url) as resp:
            if resp.status != 200:
                raise RuntimeError("Ошибка поиска на RuTracker (HTTP {})".format(resp.status))
            html = await resp.text()

        soup = BeautifulSoup(html, "html.parser")
        results = []

        for row in soup.select("tr.tCenter.hl-tr")[:5]:
            title_elem = row.select_one("a.tLink")
            magnet_elem = row.select_one("a.magnet-link")
            if not title_elem or not magnet_elem:
                continue
            title = title_elem.text.strip()
            magnet = magnet_elem.get("href")
            if title and magnet:
                results.append((title, magnet))

        return results

    except Exception as e:
        print(f"Ошибка при поиске фильма: {e}")
        return []
    finally:
        await session.close()
