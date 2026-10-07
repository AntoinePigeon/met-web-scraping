"""Run the transform over the full CSV and report coverage against the dimension spec.

Run from the repo root:  python scripts/check_transform.py
"""

import random
import re
import time

from pipeline.csv_extract import SOURCE_FILE, extract_from_csv
from pipeline.transform import transform_record

FIELDS = ("height_cm", "width_cm", "depth_cm")
SAMPLE_SIZE = 40
SEED = 42

SET_MARKER = re.compile(r"\([a-z]{1,3}\):")
LABEL_ONLY = re.compile(r"^[^:\d]*:\s*$")
TRAILING_DOT = re.compile(r"\d\.\s*cm")


def main() -> None:
    start = time.perf_counter()

    total = parsed = recovered = 0
    cm_empty = mm_empty = set_cm = 0
    label_only = trailing_dot = other_empty = 0
    l_and_w = l_and_h = lw_no_height = 0
    errors = []
    other_samples = []
    lw_samples = []

    for record in extract_from_csv(SOURCE_FILE):
        total += 1
        try:
            result = transform_record(record)
        except Exception as exc:  # deliberate: a harness counts failures instead of stopping
            errors.append((record.get("id"), record.get("dimensions"), repr(exc)))
            continue

        dims = record.get("dimensions") or ""
        has_value = any(result[field] is not None for field in FIELDS)
        has_cm = "cm" in dims
        has_in = "in." in dims
        has_mm = "mm" in dims
        is_set = bool(SET_MARKER.search(dims))

        if has_value:
            parsed += 1
        if has_value and has_in and has_mm and not has_cm:
            recovered += 1
        if has_mm and not has_cm and not has_value:
            mm_empty += 1
        if has_cm and is_set:
            set_cm += 1

        if has_cm and not has_value:
            cm_empty += 1
            if not is_set:
                first_line = dims.split("\r\n", 1)[0]
                if LABEL_ONLY.match(first_line):
                    label_only += 1
                elif TRAILING_DOT.search(dims):
                    trailing_dot += 1
                else:
                    other_empty += 1
                    other_samples.append(dims)

        has_l = "L." in dims
        if has_l and "W." in dims:
            l_and_w += 1
            if has_value and result["height_cm"] is None:
                lw_no_height += 1
                lw_samples.append((dims, {k: result[k] for k in FIELDS}))
        if has_l and "H." in dims:
            l_and_h += 1

    elapsed = time.perf_counter() - start

    print("== coverage ==")
    print(f"records:                  {total:,}")
    print(f"parsed:                   {parsed:,}")
    print(f"exceptions:               {len(errors):,}")
    print(f"time:                     {elapsed:.1f}s")
    print(f"mm recovered (in. + mm):  {recovered:,}")
    print()
    print("== empty with cm ==")
    print(f"cm empty:                 {cm_empty:,}")
    print(f"  sets:                   {set_cm:,}")
    print(f"  label-only first line:  {label_only:,}")
    print(f"  trailing dot:           {trailing_dot:,}")
    print(f"  other (incl. case 8):   {other_empty:,}")
    print(f"mm empty:                 {mm_empty:,}")
    print()
    print("== L. pairings ==")
    print(f"L. and W.:                {l_and_w:,}")
    print(f"L. and H.:                {l_and_h:,}")
    print(f"L.+W., parsed, no height: {lw_no_height:,}")

    random.seed(SEED)
    _print_sample("other empty", other_samples)
    _print_sample("L.+W., parsed, no height", lw_samples)

    for record_id, dims, exc in errors[:5]:
        print(f"  {record_id}: {exc}")
        print(f"    {dims!r}")


def _print_sample(title: str, items: list) -> None:
    """Print a reproducible random sample, never larger than the list."""
    print(f"\n== sample: {title} ==")
    for item in random.sample(items, min(SAMPLE_SIZE, len(items))):
        if isinstance(item, tuple):
            dims_text, res = item
            print(f"    {dims_text!r}")
            print(f"      -> {res}")
        else:
            print(f"    {item!r}")


if __name__ == "__main__":
    main()
