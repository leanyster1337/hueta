import aiohttp
from aiohttp_socks import ProxyConnector
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

def get_proxy_list():
    proxies = os.getenv("PROXY_URLS", "")
    # Вернём список без пробелов
    return [x.strip() for x in proxies.split(",") if x.strip()]

async def search_movie(query):
    rutracker_login = os.getenv("RUTRACKER_LOGIN")
    rutracker_password = os.getenv("RUTRACKER_PASSWORD")
    proxies = get_proxy_list()

    if not rutracker_login or not rutracker_password:
        raise RuntimeError("RUTRACKER_LOGIN или RUTRACKER_PASSWORD не заданы в .env")

    last_exc = None

    for proxy_url in proxies:
        try:
            conn = ProxyConnector.from_url(proxy_url)
            async with aiohttp.ClientSession(connector=conn) as session:
                # 1. Получаем стартовую страницу (получаем initial cookies)
                async with session.get("https://rutracker.org/forum/index.php", timeout=15) as resp:
                    if resp.status != 200:
                        raise RuntimeError(f"Ошибка соединения с RuTracker ({resp.status})")

                # 2. Авторизация
                async with session.post(
                    "https://rutracker.org/forum/login.php",
                    data={
                        "login_username": rutracker_login,
                        "login_password": rutracker_password,
                        "login": "Вход"
                    },
                    headers={
                        "User-Agent": "Mozilla/5.0",
                        "Referer": "https://rutracker.org/forum/index.php"
                    },
                    timeout=15
                ) as login_resp:
                    if login_resp.status != 200:
                        raise RuntimeError(f"Ошибка входа на RuTracker (HTTP {login_resp.status})")
                    cookies = session.cookie_jar.filter_cookies("https://rutracker.org")
                    if not cookies or "bb_session" not in cookies:
                        raise RuntimeError("Не удалось получить bb_session cookie — вход не выполнен")

                # 3. Поиск
                search_url = f"https://rutracker.org/forum/tracker.php?nm={query}"
                async with session.get(search_url, headers={"User-Agent": "Mozilla/5.0"}, timeout=20) as resp:
                    if resp.status != 200:
                        raise RuntimeError(f"Ошибка поиска на RuTracker (HTTP {resp.status})")
                    html = await resp.text()

                soup = BeautifulSoup(html, "html.parser")
                results = []
                for row in soup.select("tr.hl-tr")[:5]:
                    title_elem = row.select_one("a.tLink")
                    magnet_elem = row.select_one("a.magnet-link")
                    if not title_elem or not magnet_elem:
                        continue
                    title = title_elem.text.strip()
                    magnet = magnet_elem.get("href")
                    # Подстраховка: проверяем что этот magnet не None и начинается с magnet: (иначе это не ссылка)
                    if title and magnet and magnet.startswith("magnet:"):
                        results.append((title, magnet))

                if results:
                    return results
                # Если results пустой — пробуем следующий прокси
        except Exception as e:
            last_exc = e
            continue

    # Если ни один прокси не сработал
    if last_exc:
        raise RuntimeError(f"Не удалось получить результаты с RuTracker ни через один прокси. Последняя ошибка: {last_exc}")
    else:
        return []
