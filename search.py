import aiohttp
from bs4 import BeautifulSoup

async def search_movie(query):
    url = f"https://rutor.info/search/0/0/0/2/{query.replace(' ', '+')}"
    headers = {"User-Agent": "Mozilla/5.0"}

    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as resp:
            html = await resp.text()

    soup = BeautifulSoup(html, "html.parser")
    results = []

    for row in soup.select("tr.gai, tr.gaj")[:5]:
        link = row.select_one("a[href^='/torrent/']")
        if not link:
            continue
        title = link.text.strip()
        torrent_url = "https://rutor.info" + link["href"]

        # Переход по ссылке и поиск magnet-ссылки
        async with aiohttp.ClientSession() as session:
            async with session.get(torrent_url, headers=headers) as page:
                page_html = await page.text()
                page_soup = BeautifulSoup(page_html, "html.parser")
                magnet_link = page_soup.find("a", href=True, string="Magnet")
                if magnet_link:
                    results.append((title, magnet_link["href"]))

    return results
