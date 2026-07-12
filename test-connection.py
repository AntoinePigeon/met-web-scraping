import requests
from bs4 import BeautifulSoup
import time

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}
response = requests.get("https://www.metmuseum.org/art/collection/search", headers=headers)
time.sleep(2)
soup = BeautifulSoup(response.text, "html.parser")

print(response.status_code)
print(len(response.text))
print(response.text[:500])
print(response.headers.get("Retry-After"))