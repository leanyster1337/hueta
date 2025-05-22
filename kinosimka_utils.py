import aiohttp
from bs4 import BeautifulSoup
import re

async def get_download_url(page_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(page_url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
            html = await resp.text()
        soup = BeautifulSoup(html, "html.parser")
        # Находим iframe (обычно с видео)
        iframe = soup.find("iframe")
        if not iframe or not iframe.get("src"):
            return None
        player_url = iframe["src"]
        # Открываем страницу плеера
        async with session.get(player_url, headers={"User-Agent": "Mozilla/5.0"}) as resp2:
            html2 = await resp2.text()
        # Пытаемся вытащить mp4 или m3u8 ссылку
        mp4_match = re.search(r'(https?://[^\s"\']+\.mp4)', html2)
        if mp4_match:
            return mp4_match.group(1)
        m3u8_match = re.search(r'(https?://[^\s"\']+\.m3u8)', html2)
        if m3u8_match:
            return m3u8_match.group(1)
        # Альтернатива: ищем все ссылки в исходнике
        soup2 = BeautifulSoup(html2, "html.parser")
        for a in soup2.find_all("a"):
            href = a.get("href")
            if href and (href.endswith(".mp4") or href.endswith(".m3u8")):
                return href
        return None
