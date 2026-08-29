from pipeline.validate import check_record

def make_record(**overrides):
    """A known-good record, with optional field overrides for testing."""
    record = {
        "object_id": 999,
        "object_number": "TEST.1",
        "title": "Test Artwork",
        "maker": "Test Maker",
        "date": "1850",
        "year_start": 1850,
        "geography": None,
        "culture": "American",
        "medium": "Oil on canvas",
        "dimensions": "10 x 10 in. (25.4 x 25.4 cm)",
        "height_cm": 25.4,
        "width_cm": 25.4,
        "depth_cm": None,
        "credit_line": "Test Fund, 1900",
        "curatorial_department": "The American Wing",
    }

    record.update(overrides)
    return record


def test_valid_record_passes():
    errors = check_record(make_record())
    assert errors == []

def test_missing_title_fails():
    errors = check_record(make_record(title=None))
    assert any("is missing" in e for e in errors)

def test_year_too_high_fails():
    errors = check_record(make_record(year_start=50000))
    assert any("out of range" in e for e in errors)

def test_year_too_low_fails():
    errors = check_record(make_record(year_start=100))
    assert any("out of range" in e for e in errors)

def test_negative_dimension_fails():
    errors = check_record(make_record(height_cm=-5))
    assert any("implausible" in e for e in errors)

def test_absurd_dimension_fails():
    errors = check_record(make_record(height_cm=99999))
    assert any("implausible" in e for e in errors)