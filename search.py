import aiohttp
from bs4 import BeautifulSoup

async def search_movie(query):
    url = f"https://kinogo.biz/index.php?do=search&subaction=search&story={query}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
            html = await resp.text()
        soup = BeautifulSoup(html, "html.parser")
        results = []
        # kinogo иногда кладёт фильмы вот так:
        for a in soup.select(".th-item .th-title a"):
            title = a.text.strip()
            link = a.get("href")
            if title and link:
                results.append((title, link))
        return results
