import aiohttp
from bs4 import BeautifulSoup

async def search_movie(query):
    url = f"https://m.kinosimka.plus/index.php?do=search&subaction=search&story={query}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
            html = await resp.text()
        soup = BeautifulSoup(html, "html.parser")
        results = []
        # На мобильной версии simka фильмы обычно в .shortstory
        for movie in soup.select(".shortstory"):
            a = movie.select_one(".short-title a")
            if not a:
                continue
            title = a.text.strip()
            link = a.get("href")
            if title and link:
                # На этом сайте ссылки могут быть относительные, делаем абсолютными
                if link.startswith("/"):
                    link = f"https://m.kinosimka.plus{link}"
                results.append((title, link))
        return results
