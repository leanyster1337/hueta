import aiohttp
from bs4 import BeautifulSoup

async def search_movie(query):
    url = f"https://m.kinosimka.plus/poisk.html"
    headers = {"User-Agent": "Mozilla/5.0"}
    data = {"story": query, "do": "search", "subaction": "search"}
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data, headers=headers) as resp:
            html = await resp.text()
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for a in soup.select("a[href^='/']"):
        title = a.text.strip()
        link = a.get("href")
        # Определяем, что ссылка ведёт на страницу фильма (например, по наличию постера в родителе)
        if title and link and "/films/" in link:
            results.append((title, f"https://m.kinosimka.plus{link}"))
    return results
