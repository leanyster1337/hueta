import aiohttp
from bs4 import BeautifulSoup

async def search_movie(query):
    url = f"https://kinogo.org/index.php?do=search&subaction=search&story={query}"
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
            html = await resp.text()
        soup = BeautifulSoup(html, "html.parser")
        results = []
        # На kinogo.org фильмы обычно лежат в блоках .shortstory или .th-item
        for a in soup.select(".shortstory-title a, .th-item .th-title a"):
            title = a.text.strip()
            link = a.get("href")
            if title and link and link.startswith("http"):
                results.append((title, link))
        return results
