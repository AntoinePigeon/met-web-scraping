import requests
import json
import time
import os
import logging
import pandas as pd
from bs4 import BeautifulSoup
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Integer, String, Float, create_engine, text, Text
from sqlalchemy.dialects.postgresql import insert

# ---- logging setup (runs once) ---- #
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("pipeline.log"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)
# ---- end logging setup ---- #

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = BASE_DIR / "data" / "raw_artworks.json"
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
}

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

engine = create_engine(os.getenv("DATABASE_URL"))

# --------------------- Function ------------------------- #

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

def validate_records(records):
    valid = []
    invalid = []
    for rec in records:
        errors = check_record(rec)
        if errors:
            invalid.append((rec["object_id"], errors))
        else:
            valid.append(rec)
    return valid, invalid

def check_record(record):
    errors = []
    # -------- Check 1: required fields present -------- #
    required_fields = ["title", "medium", "year_start", "object_number", "curatorial_department", "credit_line"]
    for field in required_fields:
        if record.get(field) is None:
            errors.append(f"{record['object_id']} is missing {field}")
    
    # -------- Check 2: year sanity -------- #
    if record.get("year_start") is not None:
        if record.get("year_start") < 1500 or record.get("year_start") > datetime.now().year:
            errors.append(f"year {record.get('year_start')} is out of range")
    
    # -------- Check 3: dimension sanity -------- #
    dimension_col = ["height_cm", "width_cm", "depth_cm"]
    for col in dimension_col:
        if record.get(col) is not None:
            if record.get(col) <= 0 or record.get(col) > 2000:
                errors.append(f"{col} = {record.get(col)} implausible")
    return errors


# --------------------- Scrape Website and created JSON file ------------------------- #

# --------------Run this one time to create the data, then comment it ---------------- #

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
#     logger.info(f"offset {offset}: got {len(new_ids)} ids")
#     time.sleep(2)

# for i, oid in enumerate(sorted(all_ids)):
#     try:
#         new_artwork = scrape_artwork(oid)
#         all_artworks.append(new_artwork)
#     except Exception as e:
#         logger.error(f"Failed on {oid}: {e}")
#         failed_count += 1
#     logger.info(f"[{i+1}/{len(all_ids)}] scraped {new_artwork['Title']}")
#     time.sleep(2)

# logger.info(f"\nFailed -> {failed_count}\n")

# with open(OUTPUT_FILE, "w") as f:
#     json.dump(all_artworks, f, indent=2)


# --------------------- Cleaning Save Data ------------------------- #

with open(OUTPUT_FILE, "r") as f:
    all_artworks = json.load(f)

df = pd.DataFrame(all_artworks)

# Clean columns
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

# Clean dates
df["year_start"] = df['date'].str.extract(r'(\d{4})')
df["year_start"] = df["year_start"].astype("Int64")

# Clean dimensions
df['dimensions'] = df['dimensions'].str.replace('×', 'x')
df['dimension_cm'] = df['dimensions'].str.extract(r'\(([\d.\sx]+?)\s*cm')
df[['height_cm', 'width_cm', 'depth_cm']] = df['dimension_cm'].str.split('x', expand=True)
df['height_cm'] = df['height_cm'].astype(float)
df['width_cm'] = df['width_cm'].astype(float)
df['depth_cm'] = df['depth_cm'].astype(float)
df = df.drop(columns=['dimension_cm']) 

# --------------------- Table Creation ------------------------- #

class Base(DeclarativeBase):
    pass

class Artworks(Base):
    __tablename__ = "artworks"

    object_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    object_number: Mapped[str] = mapped_column(String(32), unique=True)
    title: Mapped[str] = mapped_column(Text)
    maker: Mapped[str | None] = mapped_column(Text)
    date: Mapped[str] = mapped_column(Text)
    year_start: Mapped[int] = mapped_column(Integer)
    geography: Mapped[str | None] = mapped_column(Text)
    culture: Mapped[str | None] = mapped_column(Text)
    medium: Mapped[str] = mapped_column(Text)
    dimensions: Mapped[str | None] = mapped_column(Text)
    height_cm: Mapped[float | None] = mapped_column(Float)
    width_cm: Mapped[float | None] = mapped_column(Float)
    depth_cm: Mapped[float | None] = mapped_column(Float)
    credit_line: Mapped[str] = mapped_column(Text)
    curatorial_department: Mapped[str] = mapped_column(Text)

Base.metadata.create_all(engine)

# --------------------- the idempotent load ------------------------- #

clean_df = df.astype(object).where(df.notna(), None)
records = clean_df.to_dict(orient="records")

# records[1]["title"] = None # test check 1
# records[2]["year_start"] = 50000 # test check 2
# records[3]["height_cm"] = -5 # test check 3

valid, invalid = validate_records(records)

logger.info(f"{len(valid)} valid, {len(invalid)} invalid")
for object_id, errors in invalid:
    logger.warning(f"  ✗ {object_id}: {errors}")

stmt = insert(Artworks).values(valid)

update_columns = [col for col in Artworks.__table__.columns.keys() if col != "object_id"]

stmt = stmt.on_conflict_do_update(
    index_elements=["object_id"],
    set_={col: stmt.excluded[col] for col in update_columns},
)

with engine.begin() as conn:
    conn.execute(stmt)

logger.info(f"Upserted {len(valid)} records!")