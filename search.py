import aiohttp
from bs4 import BeautifulSoup

async def search_movie(query):
    url = f"https://m.kinosimka.plus/index.php?do=search&subaction=search&story={query}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
            html = await resp.text()
    print(html[:2000])  # <--- добавь эту строку для отладки!
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for movie in soup.select(".shortstory"):
        a = movie.select_one(".short-title a")
        if not a:
            continue
        title = a.text.strip()
        link = a.get("href")
        if title and link:
            if link.startswith("/"):
                link = f"https://m.kinosimka.plus{link}"
            results.append((title, link))
    return results
