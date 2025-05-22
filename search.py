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
    # Каждый фильм — это блок с <a> (с названием) и постером
    for div in soup.find_all("div", class_="content"):
        a = div.find("a")
        title = a.text.strip() if a else None
        link = a.get("href") if a else None
        if title and link:
            if link.startswith("/"):
                link = f"https://m.kinosimka.plus{link}"
            results.append((title, link))
    return results
