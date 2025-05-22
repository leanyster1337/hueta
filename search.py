import aiohttp
from bs4 import BeautifulSoup

async def search_movie(query):
    url = f"https://kinogo.biz/index.php?do=search&subaction=search&story={query}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
            if resp.status != 200:
                raise RuntimeError(f"Ошибка поиска на kinogo.org (HTTP {resp.status})")
            html = await resp.text()

        soup = BeautifulSoup(html, "html.parser")
        results = []
        for movie in soup.select(".shortstory")[:8]:
            title_tag = movie.select_one(".shortstory-title a")
            if not title_tag:
                continue
            title = title_tag.text.strip()
            link = title_tag.get("href")
            if title and link:
                results.append((title, link))
        return results
