from pipeline.validate import check_record


def make_record(**overrides):
    """A known-good record, with optional field overrides for testing."""
    record = {
        "id": 999,
        "number": "TEST.1",
        "highlight": False,
        "department": "The American Wing",
        "name": "Test Artwork",
        "title": "Test Artwork",
        "culture": "American",
        "medium": "Oil on canvas",
        "classification": "Painting",
        "dimensions": "10 x 10 in. (25.4 x 25.4 cm)",
        "height_cm": 25.4,
        "width_cm": 25.4,
        "depth_cm": None,
        "date": "1850",
        "year_start": 1850,
        "year_end": 1851,
        "artist_name": "Test Artist",
        "credit_line": "Test Fund, 1900",
        "link": "https://www.metmuseum.org/art/collection/search/999",
    }

    record.update(overrides)
    return record


def test_valid_record_passes():
    errors = check_record(make_record())
    assert errors == []


def test_missing_id_fails():
    errors = check_record(make_record(id=None))
    assert any("is missing" in e for e in errors)


def test_missing_year_end_fails():
    errors = check_record(make_record(year_end=None))
    assert any("is missing" in e for e in errors)


def test_missing_year_start_fails():
    errors = check_record(make_record(year_start=None))
    assert any("is missing" in e for e in errors)


def test_year_start_after_year_end_fails():
    errors = check_record(make_record(year_start=1900, year_end=1850))
    assert any("is later than" in e for e in errors)


def test_future_year_end_fails():
    errors = check_record(make_record(year_end=2870))
    assert any("is later than the current year" in e for e in errors)


# def test_negative_dimension_fails():
#     errors = check_record(make_record(height_cm=-5))
#     assert any("implausible" in e for e in errors)

# def test_absurd_dimension_fails():
#     errors = check_record(make_record(height_cm=99999))
#     assert any("implausible" in e for e in errors)
