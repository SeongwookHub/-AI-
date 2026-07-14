from backend.services.validators import (
    dedup_by_link,
    validate_article_schema,
    validate_keyword_input,
)


def test_validate_keyword_input_rejects_empty():
    ok, error = validate_keyword_input("   ", [])
    assert not ok
    assert "빈 값" in error


def test_validate_keyword_input_rejects_duplicate():
    ok, error = validate_keyword_input("반도체", ["반도체"])
    assert not ok
    assert "이미 등록" in error


def test_validate_keyword_input_accepts_new():
    ok, error = validate_keyword_input("2차전지", ["반도체"])
    assert ok
    assert error == ""


def test_validate_article_schema_splits_valid_invalid():
    items = [
        {"title": "A", "link": "http://a", "pub_date": "2026-07-14"},
        {"title": "B", "link": "http://b"},  # pub_date 누락
        {"link": "http://c", "pub_date": "2026-07-14"},  # title 누락
    ]
    valid, invalid = validate_article_schema(items)
    assert len(valid) == 1
    assert len(invalid) == 2


def test_dedup_by_link_removes_duplicates_preserving_order():
    items = [
        {"link": "http://a", "title": "1"},
        {"link": "http://b", "title": "2"},
        {"link": "http://a", "title": "1-dup"},
    ]
    deduped = dedup_by_link(items)
    assert [i["link"] for i in deduped] == ["http://a", "http://b"]
