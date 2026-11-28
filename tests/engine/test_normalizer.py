import time

from engine.core.normalizer import MAX_INPUT_LENGTH, normalize


def test_single_and_double_url_decoding():
    assert normalize("%2e%2e%2f") == "../"
    assert normalize("%252e%252e%252f") == "../"


def test_round_limit_stops_deep_encoding():
    # 10-times URL-encoded "." (%2e -> %252e -> ... -> %25...2e)
    encoded = "."
    for _ in range(10):
        encoded = encoded.replace("%", "%25").replace(".", "%2e")

    result = normalize(encoded, max_rounds=3)
    assert result != "."
    assert "%" in result


def test_null_bytes_removed():
    assert normalize("admin\x00.php") == "admin.php"
    assert normalize("admin%00.php") == "admin.php"
    assert normalize("admin%2500.php") == "admin.php"


def test_unicode_nfkc_fullwidth_slash():
    assert normalize("\uff0fetc\uff0fpasswd") == "/etc/passwd"


def test_lowercase_and_whitespace_collapsed():
    assert normalize("UNION   \t\n  SELECT   1") == "union select 1"


def test_plus_as_space():
    assert normalize("select+1+from+users", plus_as_space=False) == "select+1+from+users"
    assert normalize("select+1+from+users", plus_as_space=True) == "select 1 from users"


def test_dot_dot_preserved():
    assert normalize("/static/../../etc/passwd") == "/static/../../etc/passwd"
    assert normalize("%2e%2e/%2e%2e/etc/passwd") == "../../etc/passwd"


def test_empty_string_and_strange_inputs():
    assert normalize("") == ""
    assert normalize("%ZZ%invalid%") == "%zz%invalid%"
    assert normalize(None) == ""  # type: ignore[arg-type]


def test_huge_input_bounded_and_fast():
    huge = "A" * 1_000_000
    start = time.perf_counter()
    result = normalize(huge)
    elapsed = time.perf_counter() - start

    assert len(result) == MAX_INPUT_LENGTH
    assert result == "a" * MAX_INPUT_LENGTH
    assert elapsed < 0.5
