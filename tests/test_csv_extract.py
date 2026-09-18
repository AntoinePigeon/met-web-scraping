from pathlib import Path

from pipeline.csv_extract import COLUMN_MAP, extract_from_csv

FIXTURE = Path(__file__).parent / "fixtures" / "met_sample.csv"


def test_emits_contract_field_names():
    records = list(extract_from_csv(FIXTURE, limit=5))
    expected = set(COLUMN_MAP.values())
    assert records, "adapter yielded nothing"
    for record in records:
        assert set(record.keys()) == expected


def test_limit_is_respected():
    assert len(list(extract_from_csv(FIXTURE, limit=3))) == 3
