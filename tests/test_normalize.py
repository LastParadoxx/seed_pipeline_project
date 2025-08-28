from seed_pipeline.normalize.text import normalize_seed, normalize_variation, md5_hex


def test_normalization_simple():
    assert normalize_seed("  Michaël  ") == "michael"
    assert normalize_variation("AuTumn") == "autumn"
    # ensure whitespace collapse
    assert normalize_seed("John   Doe") == "john doe"


def test_md5():
    text = "example"
    assert md5_hex(text) == "1a79a4d60de6718e8e5b326e338ae533"