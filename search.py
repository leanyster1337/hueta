import requests
from bs4 import BeautifulSoup

def search_movie(query):
    url = f"https://rutor.info/search/{query.replace(' ', '%20')}"
    response = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
    soup = BeautifulSoup(response.text, "html.parser")
    results = soup.select("a[href^='magnet:']")
    return [link['href'] for link in results][:5]