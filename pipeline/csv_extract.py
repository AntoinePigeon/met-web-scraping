import itertools
import time
from collections.abc import Iterator
from pathlib import Path

import pandas as pd

BASE_DIR = Path(__file__).resolve().parent.parent
SOURCE_FILE = BASE_DIR / "data" / "MetObjects.txt"

COLUMN_MAP = {
    "Object ID": "id",
    "Is Highlight": "highlight",
    "Department": "department",
    "Title": "title",
    "Culture": "culture",
    "Medium": "medium",
    "Classification": "classification",
    "Dimensions": "dimensions",
    "Object Number": "number",
    "Object Name": "name",
    "Object Date": "date",
    "Object Begin Date": "year_start",
    "Object End Date": "year_end",
    "Artist Display Name": "artist_name",
    "Artist Role": "artist_role",
    "Artist Display Bio": "artist_bio",
    "Artist Nationality": "artist_nationality",
    "Artist Begin Date": "artist_birth",
    "Artist End Date": "artist_death",
    "Credit Line": "credit_line",
    "City": "city",
    "State": "state",
    "County": "county",
    "Country": "country",
    "Region": "region",
    "Subregion": "subregion",
    "Rights and Reproduction": "rights",
    "Link Resource": "link",
    "AccessionYear": "accession_year",
}


def _read_all(path: Path) -> Iterator[dict]:
    """Yield every public-domain record. No limit."""
    with pd.read_csv(path, chunksize=500, na_values=["", " ", "N/A", "-"]) as reader:
        for chunk in reader:
            # filter to public-domain objects
            chunk = chunk[chunk["Is Public Domain"]]
            # rename columns to match contract field names
            chunk = chunk[list(COLUMN_MAP.keys())].rename(columns=COLUMN_MAP)
            chunk["accession_year"] = (
                chunk["accession_year"]
                .astype(str)
                .str.extract(r"^(\d{4})", expand=False)
                .astype("Int64")
            )

            for record in chunk.to_dict(orient="records"):
                clean_record = {
                    key: (None if pd.isna(value) else value) for key, value in record.items()
                }
                yield clean_record


def extract_from_csv(path: Path, limit: int | None = None) -> Iterator[dict]:
    """Yield Met artwork records from the bulk CSV, in extract-contract shape.

    Reads the Met's published bulk dump, keeps only public-domain objects, and
    renames source columns to contract field names. Downstream stages receive
    the same shape regardless of which extract source produced it.

    Does not validate, parse dimensions, or touch the database.

    Args:
        path: Location of the Met bulk CSV (MetObjects.txt).
        limit: Stop after this many public-domain records. None reads all.

    Yields:
        One record per public-domain object, keyed by contract field names.
    """
    yield from itertools.islice(_read_all(path), limit)


if __name__ == "__main__":
    start_time = time.perf_counter()
    count = 0
    accession_present = 0

    records = extract_from_csv(SOURCE_FILE)
    for record in records:
        count += 1
        if record["accession_year"] is not None:
            accession_present += 1

    end_time = time.perf_counter()
    execution_time = end_time - start_time

    print(f"{count} records in {execution_time:.1f} seconds")
    print(f"accession_year present: {accession_present}")
