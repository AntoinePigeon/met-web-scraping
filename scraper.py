import json
import requests
import time
from config import logger, OUTPUT_FILE
from bs4 import BeautifulSoup

from config import HEADERS


def scrape_all():
    """Scrape the collection and save the raw records to OUTPUT_FILE."""
    base_url = "https://www.metmuseum.org/art/collection/search?department=The+American+Wing"
    offset = 0
    page_count = 0
    failed_count = 0
    all_ids = set()
    all_artworks = []

    while True:
        if page_count >= 3:
            break
        new_ids = harvest_ids(f"{base_url}&offset={offset}")
        if not new_ids:
            break
        all_ids.update(new_ids)
        offset += 42
        page_count += 1
        logger.info(f"offset {offset}: got {len(new_ids)} ids")
        time.sleep(2)

    for i, oid in enumerate(sorted(all_ids)):
        try:
            new_artwork = scrape_artwork(oid)
            all_artworks.append(new_artwork)
        except Exception as e:
            logger.error(f"Failed on {oid}: {e}")
            failed_count += 1
        logger.info(f"[{i+1}/{len(all_ids)}] scraped {new_artwork['Title']}")
        time.sleep(2)

    logger.info(f"\nFailed -> {failed_count}\n")

    with open(OUTPUT_FILE, "w") as f:
        json.dump(all_artworks, f, indent=2)
    
    logger.info(f"Scrape complete: {len(all_artworks)} records saved, {failed_count} failed")


def scrape_artwork(object_id):
    """Return a full record for one object ID."""
    url = f"https://www.metmuseum.org/art/collection/search/{object_id}"

    response = requests.get(url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    data = {}

    # Tombstone overview
    tombstone = soup.select_one("[class*='tombstone']")
    for li in tombstone.select("li"):
        label = li.find("strong").get_text(strip=True).replace(":", "")
        value = li.get_text(strip=True).removeprefix(label + ":")
        data[label] = value

    # objectID from the analytics JSON script
    script = soup.find("script", id="analytics")
    analytics_data = json.loads(script.get_text())
    data["objectID"] = analytics_data["objectID"]

    return data


def harvest_ids(listing_url):
    """Return a list of object IDs found on one listing page."""
    response = requests.get(listing_url, headers=HEADERS, timeout=10)
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    ids = set()
    for tag in soup.select("a[href*='/art/collection/search/']"):
        ids.add(int(tag["href"].split("/")[-1]))

    return list(ids)