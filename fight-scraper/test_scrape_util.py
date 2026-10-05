from scrape_util import normalize_fighter_tag, parse_height_cm


def test_parse_height_cm_converts_feet_and_inches():
    assert parse_height_cm("5' 10\"") == 177.8


def test_parse_height_cm_accepts_missing_profile_measurement():
    assert parse_height_cm("--") == 0.0


def test_parse_height_cm_accepts_malformed_measurement_without_raising():
    assert parse_height_cm("unknown") == 0.0


def test_normalize_fighter_tag_preserves_jr_suffix():
    assert normalize_fighter_tag("Raul Rosas Jr.") == "raul_rosas_jr."
