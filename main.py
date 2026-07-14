import requests
import json
import time
from bs4 import BeautifulSoup
import pandas as pd

HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
}

def scrape_artwork(object_id):
    """ Return a full record for one ID """
    URL = f"https://www.metmuseum.org/art/collection/search/{object_id}"

    response = requests.get(URL, headers=HEADERS, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    data = {}

# Get the overview info
    tombstone = soup.select_one("[class*='tombstone']")
    tombstone_ls = tombstone.select("li")
    for li in tombstone_ls:
        label = li.find("strong").get_text(strip=True).replace(":", "")
        value = li.get_text(strip=True).removeprefix(label + ":")
        data[label] = value

# Get the object ID
    script = soup.find("script", id="analytics")
    text = script.get_text()
    analytics_data = json.loads(text)
    object_id_value = analytics_data["objectID"]
    data["objectID"] = object_id_value

    return data

def harvest_ids(listing_url):
    """ Return a list of objects IDs """
    response = requests.get(listing_url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    ids = set()
    anchors = soup.select("a[href*='/art/collection/search/']")
    for tag in anchors:
        href = tag["href"]
        object_id = int(href.split("/")[-1])
        ids.add(object_id)

    return list(ids)


# --------------------- Scrape Website and created JSON file ------------------------- #
# base_url = "https://www.metmuseum.org/art/collection/search?department=The+American+Wing"
# offset = 0
# page_count = 0
# failed_count = 0

# all_ids = set()
# all_artworks = []

# while True:
#     if page_count >= 3:
#         break
#     new_ids = harvest_ids(f"{base_url}&offset={offset}")
#     if not new_ids:
#         break
#     all_ids.update(new_ids)
#     offset += 42
#     page_count += 1
#     print(f"offset {offset}: got {len(new_ids)} ids")
#     time.sleep(2)

# for i, oid in enumerate(sorted(all_ids)):
#     try:
#         new_artwork = scrape_artwork(oid)
#         all_artworks.append(new_artwork)
#     except Exception as e:
#         print(f"Failed on {oid}: {e}")
#         failed_count += 1
#     print(f"[{i+1}/{len(all_ids)}] scraped {new_artwork['Title']}")
#     time.sleep(2)

# print(f"\nFailed -> {failed_count}\n")

# with open("raw_artworks.json", "w") as f:
#     json.dump(all_artworks, f, indent=2)


# --------------------- CLeaning Save Data ------------------------- #

with open("raw_artworks.json", "r") as f:
    all_artworks = json.load(f)

df = pd.DataFrame(all_artworks)

df["maker"] = (df["Artist"]
    .combine_first(df["Maker"])
    .combine_first(df["Manufacturer"])
    .combine_first(df["Designer"])
    .combine_first(df["Decorator"])
    .combine_first(df["Architect"])
    .combine_first(df["Founder"]))

df = df.drop(columns=["Artist","Maker", "Manufacturer", "Designer", "Decorator", "Architect", "Founder", "Rights and Reproduction"])

df = df.rename(columns={"Title": "title",
                        "Date": "date",
                        "Geography": "geography",
                        "Culture": "culture",
                        "Medium": "medium",
                        "Dimensions": "dimensions",
                        "Credit Line": "credit_line",
                        "Object Number": "object_number",
                        "Curatorial Department": "curatorial_department",
                        "objectID": "object_id"})

df["year_start"] = df['date'].str.extract(r'(\d{4})')

df["year_start"] = df["year_start"].astype("Int64")

print(df["year_start"])
df.info()