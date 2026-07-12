import requests
from bs4 import BeautifulSoup

URL = "https://www.metmuseum.org/art/collection/search/16584"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

response = requests.get(URL, headers=HEADERS, timeout=10)
response.raise_for_status
soup = BeautifulSoup(response.text, "html.parser")

data = {}

tombstone = soup.select_one("[class*='tombstone']")
tombstone_ls = tombstone.select("li")

for li in tombstone_ls:
    label = li.find("strong").get_text(strip=True).replace(":", "")
    value = li.get_text(strip=True).removeprefix(label + ":")
    data[label] = value

print(data)