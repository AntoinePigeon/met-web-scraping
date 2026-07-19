import json

from config import OUTPUT_FILE, logger
from scraper import scrape_all
from transform import clean_data
from validate import validate_records
from database import init_db, load_records


def main():
    # 1. EXTRACT — uncomment to refresh the raw data from the Met
    # scrape_all()

    # Load the cached raw extract
    with open(OUTPUT_FILE, "r") as f:
        all_artworks = json.load(f)
    logger.info(f"Loaded {len(all_artworks)} raw records")

    # 2. TRANSFORM
    df = clean_data(all_artworks)
    clean_df = df.astype(object).where(df.notna(), None)
    records = clean_df.to_dict(orient="records")

    # 3. VALIDATE
    valid, invalid = validate_records(records)
    logger.info(f"{len(valid)} valid, {len(invalid)} invalid")
    for object_id, errors in invalid:
        logger.warning(f"  ✗ {object_id}: {errors}")

    # 4. LOAD
    init_db()
    load_records(valid)


if __name__ == "__main__":
    main()