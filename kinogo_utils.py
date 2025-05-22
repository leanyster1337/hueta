import aiohttp
from bs4 import BeautifulSoup
import re

async def get_download_url(page_url):
    async with aiohttp.ClientSession() as session:
        async with session.get(page_url, headers={"User-Agent": "Mozilla/5.0"}) as resp:
            html = await resp.text()

        soup = BeautifulSoup(html, "html.parser")
        # Находим таб с "Плеер 3" (может отличаться по сайту, корректируй если не работает)
        player3_tab = soup.find(lambda tag: tag.name == "a" and "Плеер 3" in tag.text)
        if not player3_tab or not player3_tab.get("data-toggle"):
            # Иногда табы реализованы иначе, ищи нужный id или класс
            return None

        player3_id = player3_tab.get("href", "").replace("#", "")
        player3_div = soup.find(id=player3_id)
        if not player3_div:
            return None

        # Внутри player3_div ищем iframe или скрипт с src на видеохостинг
        iframe = player3_div.find("iframe")
        if iframe and iframe.get("src"):
            player3_url = iframe["src"]
        else:
            # Иногда видео ссылка в data-src или в JS (может потребоваться доработка)
            player3_url = None

        # Теперь пытаемся открыть player3_url и найти прямую ссылку на видео (или ссылку на скачивание)
        if not player3_url:
            return None

        # Открываем плеер 3 (часто там вложенный iframe или прямая ссылка)
        async with session.get(player3_url, headers={"User-Agent": "Mozilla/5.0"}) as resp2:
            html2 = await resp2.text()

        # Пытаемся найти .mp4 или .m3u8 прямую ссылку
        video_url = None
        mp4_match = re.search(r'(https?://[^\s"\']+\.mp4)', html2)
        if mp4_match:
            video_url = mp4_match.group(1)
        else:
            # Попробуй найти .m3u8 (HLS), если не нашёл mp4
            m3u8_match = re.search(r'(https?://[^\s"\']+\.m3u8)', html2)
            if m3u8_match:
                video_url = m3u8_match.group(1)

        # Альтернатива: иногда есть кнопка/иконка "скачать" — ищем ссылку <a> с иконкой
        soup2 = BeautifulSoup(html2, "html.parser")
        download_btn = soup2.find("a", {"title": "Скачать"})
        if download_btn and download_btn.get("href"):
            video_url = download_btn["href"]

        return video_url
