from datetime import datetime


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