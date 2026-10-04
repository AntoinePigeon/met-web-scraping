"""Transform stage: parse contract-shape records into loadable ones.

Source-agnostic. Receives records from any extract adapter, in extract-contract shape.
"""

import re


SENTINELS = [
    "dimensions unavailable",
    "n.a.",
    "various",
    "[no dimensions available]",
    "no measurement",
    "various dimensions",
    "dimensions unrecorded",
    "not available",
]

AXIS_LABELS = {
    "H.": "height_cm",
    "W.": "width_cm",
    "D.": "depth_cm",
    "Diam.": "width_cm",
    "L.": "width_cm",
}

FIELD_ORDER = ["height_cm", "width_cm", "depth_cm"]

NUMBER = r"\d*\.?\d+"

def parse_line(line: str, unit: str = "cm") -> dict[str, float | None]:
    """Parse one line of a dimension string into height, width, depth.

    Normalise × to x. Split on ";". For each segment, drop a leading label
    (non-digit text ending in a colon). If the segment starts with an axis
    label, its first number before the unit fills that field. Otherwise the
    unit block fills height, width, depth by position. Fields already set are
    not overwritten.
    """

    result = {field: None for field in FIELD_ORDER}

    line = line.replace("×", "x")

    for segment in line.split(";"):
        segment = segment.strip()

        segment = re.sub(r"^[^:\d]*:\s*", "", segment)

        field = None
        for label, target in AXIS_LABELS.items():
            if segment.startswith(label):
                field = target
                break

        if field is not None:
            match = re.search(rf"({NUMBER})\s*{unit}", segment)
            if match and result[field] is None:
                result[field] = float(match.group(1))
            continue

        match = re.search(rf"({NUMBER}(?:\s*x\s*{NUMBER})*)\s*{unit}", segment)
        if match:
            numbers = match.group(1).split("x")
            for field_name, value in zip(FIELD_ORDER, numbers):
                if result[field_name] is None:
                    result[field_name] = float(value)

    return result

def _empty() -> dict[str, float | None]:
    return {field: None for field in FIELD_ORDER}

def parse_dimensions(text: str | None) -> dict[str, float | None]:
    """Apply the dimension spec's cases, in precedence order, to a full string."""

    # 1. null
    if text is None:
        return _empty()

    # 2. sentinel
    if text.lower().strip() in SENTINELS:
        return _empty()

    has_cm = "cm" in text
    cm_count = text.count("cm")

    # 3. set markers
    if has_cm and re.search(r"\([a-z]{1,3}\):", text):
        return _empty()

    # 4. single measurement
    if has_cm and cm_count < 2:
        return parse_line(text)

    # 5, 6, 7. multi: parse the first line
    if has_cm and cm_count >= 2:
        first_line = text.split("\r\n", 1)[0]
        if re.search(r"^[A-Za-z ]+:", first_line) or "cm" in first_line:
            return parse_line(first_line)

    # 8. cm, anything else
    if has_cm:
        return _empty()

    # 10. mm only
    if "mm" in text:
        parsed_mm = parse_line(text, unit="mm")
        return {key: (value/10 if value is not None else None) for key, value in parsed_mm.items()}

    # 9, 11. everything else
    return _empty()


def transform_record(record: dict) -> dict:
    """Return a new record with parsed dimension fields added. Does not mutate the input.

    The raw `dimensions` string is kept unchanged alongside the parsed
    `height_cm`, `width_cm`, and `depth_cm`.
    """

    raw = record.get("dimensions")
    parsed = parse_dimensions(raw)
    return {**record, **parsed}
