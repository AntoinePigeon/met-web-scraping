from datetime import date

today_year = date.today().year


def check_record(record):
    errors = []

    # -------- Check 1: required fields present -------- #

    # The following fields are required for the API to function.
    # They should be present in every record.
    # NOT-NULL counts = 0 in the source CSV, measured 2026-09-10 against public-domain set.

    required_fields = [
        "id",
        "number",
        "highlight",
        "department",
        "year_start",
        "year_end",
        "link",
    ]
    for field in required_fields:
        if record.get(field) is None:
            errors.append(f"{field} is missing")

    # -------- Check 2: year sanity -------- #

    # The following checks are performed on the year_start and year_end fields:
    # 1. year_start and year_end must be present (checked above)
    # 2. year_start and year_end must be less than or equal to the current year (no future dates)
    # 3. year_start must be less than or equal to year_end (no negative durations)

    # Remove the 1500 bound check, since the Met has objects from before 1500.
    # Was measured against the public-domain set, 2026-09-10, and found 84365 records with start year < 1500

    record_year_start = record.get("year_start")
    record_year_end = record.get("year_end")

    if record_year_start is not None and record_year_end is not None:
        if record_year_start > today_year:
            errors.append(f"year {record_year_start} is in the future")
        if record_year_end > today_year:
            # Measured 2026-09-10 against public-domain set, found 2 records with end year > 2026
            # 1. 2870, typo for 1870
            # 2. 2099, one a century sentinel the Met uses for open-ended modern works
            errors.append(f"year {record_year_end} is later than the current year {today_year}")
        if record_year_start > record_year_end:
            # 147 rows, measured 2026-09-10 against public-domain set.
            errors.append(f"year {record_year_start} is later than {record_year_end}")

    # -------- Check 3: dimension sanity -------- #
    # TODO: Dimension bounds (<= 0, > 2000) cannot be measured pre-transform.
    # The parsed columns do not exist in the source.
    # Bounds were set against 126 American Wing objects and must be re-measured after the transform runs at scale.

    # dimension_col = ["height_cm", "width_cm", "depth_cm"]
    # for col in dimension_col:
    #     if record.get(col) is not None:
    #         if record.get(col) <= 0 or record.get(col) > 2000:
    #             errors.append(f"{col} = {record.get(col)} implausible")

    return errors


def validate_records(records):
    valid = []
    invalid = []
    for rec in records:
        errors = check_record(rec)
        if errors:
            identifier = rec.get("number") or rec.get("id") or "<no identifier>"
            invalid.append((identifier, errors))
        else:
            valid.append(rec)
    return valid, invalid
