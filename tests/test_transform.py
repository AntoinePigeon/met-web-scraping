import pytest

from pipeline.transform import parse_dimensions, parse_line, transform_record


def dims(h=None, w=None, d=None):
    return {"height_cm": h, "width_cm": w, "depth_cm": d}


EMPTY = dims()


# -------- parse_line: the shared rule -------- #

@pytest.mark.parametrize(
    "line, expected",
    [
        # positional
        ("44 3/4 x 23 1/2 x 15 3/4 in. (113.7 x 59.7 x 40 cm)", dims(113.7, 59.7, 40.0)),
        ("11 x 9 in. (27.9 x 22.9 cm)", dims(27.9, 22.9)),
        ("10.5 x 7 x 0.5 cm (4 1/8 x 2 3/4 x 3/16 in.)", dims(10.5, 7.0, 0.5)),
        ("19 3/4 × 23 3/4 in. (50.2 × 60.3 cm)", dims(50.2, 60.3)),
        ("(54.6 × 57.5 × 35.2 cm, 49.9 kg)", dims(54.6, 57.5, 35.2)),
        # single axis label
        ("H. 12 in. (30.5 cm)", dims(h=30.5)),
        ("Diam. 3 in. (7.6 cm)", dims(w=7.6)),
        # labelled axes across segments
        ("H. 6 9/16 in. (16.7 cm); Diam. 3 in. (7.6 cm)", dims(h=16.7, w=7.6)),
        ("H. 2 1/16 in. (5.2 cm); D. 4 15/16 in. (12.5 cm)", dims(h=5.2, d=12.5)),
        # numbers not followed by cm are ignored
        ("H. 5 in. (12.7 cm); W. 5 7/8 in. (14.9 cm); Wt. 2.5 oz. (70 g)", dims(h=12.7, w=14.9)),
        ("Overall: H. 2 7/16 in. (6.2 cm); 3 oz. 19 dwt. (123.3 g)", dims(h=6.2)),
        # a field already set is not overwritten
        ("H. 10 in. (25.4 cm); H. with lid 12 in. (30.5 cm)", dims(h=25.4)),
        # a leading component label is dropped before axis matching
        ("Backplate: Diam. 2 3/4 in. (7 cm)", dims(w=7.0)),
        ("Sheet (confirmed): 12 x 9 in. (30.5 x 22.9 cm)", dims(30.5, 22.9)),
        ("Ring pull: Diam. 1 in. (2.5 cm)", dims(w=2.5)),
        ("12 x 9 in. (30.5 x 22.9 cm)\r\nMat: 20 x 16 in.", dims(30.5, 22.9)),
    ],
)
def test_parse_line(line, expected):
    assert parse_line(line) == expected


# -------- parse_dimensions: the cases, in precedence order -------- #

@pytest.mark.parametrize(
    "text, expected",
    [
        # 1. null
        (None, EMPTY),
        # 2. sentinels, case and whitespace normalised
        ("Dimensions unavailable", EMPTY),
        ("  Various ", EMPTY),
        # 3. sets
        ("(a): 94 x 62 in. (238.8 x 157.5 cm)\r\n(b): 94 x 31 1/2 in. (238.8 x 80 cm)", EMPTY),
        # 5. multi, first line Overall
        ("Overall: 12 x 10 in. (30.5 x 25.4 cm)\r\nBase: 4 x 4 in. (10.2 x 10.2 cm)",
        dims(30.5, 25.4)),
        # 6. multi, first line component
        ("Backplate: 4 7/8 x 4 1/4 in. (12.4 x 10.8 cm)\r\nRing pull: Diam. 1 in. (2.5 cm)",
        dims(12.4, 10.8)),
        # 7. multi, first line unlabelled
        ("24 7/8 x 20 11/16 x 1 in. (63.2 x 52.5 x 2.5 cm)\r\nSight: 22 1/16 x 17 13/16 in. (56 x 45.2 cm)",
        dims(63.2, 52.5, 2.5)),
        # 8. cm, anything else
        ("L. 24 1/2 x W. 5 1/2 to 6 3/4 inches\r\n62.2 x 14.0 cm to 17.1 cm", EMPTY),
        # 10. mm only, divided by 10
        ("Diam. 76 mm", dims(w=7.6)),
        ("Diam. 3 in. (76 mm)", dims(w=7.6)),
        # 9. inches only
        ("Length 3-1/2 in.", EMPTY),
        # 11. other
        ("12 x 165 ft. (3.6 x 49.5 m)", EMPTY),
    ],
)
def test_parse_dimensions(text, expected):
    assert parse_dimensions(text) == expected


# -------- transform_record: the stage interface -------- #

def test_transform_record_adds_parsed_fields_and_keeps_raw():
    record = {"id": 1, "dimensions": "H. 12 in. (30.5 cm)"}
    result = transform_record(record)
    assert result["dimensions"] == "H. 12 in. (30.5 cm)"
    assert result["height_cm"] == 30.5
    assert result["width_cm"] is None
    assert result["depth_cm"] is None


def test_transform_record_does_not_mutate_input():
    record = {"id": 1, "dimensions": "H. 12 in. (30.5 cm)"}
    transform_record(record)
    assert "height_cm" not in record