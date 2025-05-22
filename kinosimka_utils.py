import aiohttp
from bs4 import BeautifulSoup

async def get_download_links(page_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(page_url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
            html = await resp.text()
    soup = BeautifulSoup(html, "html.parser")
    results = []
    for a in soup.find_all("a"):
        href = a.get("href", "")
        text = a.get_text(strip=True)
        if href.endswith(".mp4") and "Скачать" in text:
            # Извлекаем качество из соседнего тэга (например, 320x240 или 720x304)
            parent = a.parent
            quality = None
            if parent:
                q_tag = parent.find(string=lambda t: "x" in t and " " not in t)
                if q_tag:
                    quality = q_tag.strip()
            results.append({
                "text": text,
                "url": href if href.startswith("http") else f"https://m.kinosimka.plus{href}",
                "quality": quality
            })
    # Фильтруем только 320 и 720
    filtered = []
    for r in results:
        q = r["quality"] or ""
        if "720" in q or "320" in q:
            filtered.append(r)
    return filtered
