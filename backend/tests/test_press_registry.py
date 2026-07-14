from backend.services.press_registry import filter_allowed_articles, is_allowed_link


def test_is_allowed_link_matches_exact_domain():
    assert is_allowed_link("https://www.yna.co.kr/view/123", {"yna.co.kr"})


def test_is_allowed_link_matches_subdomain():
    assert is_allowed_link("https://biz.sbs.co.kr/article/123", {"sbs.co.kr"})


def test_is_allowed_link_rejects_unrelated_domain():
    assert not is_allowed_link("https://example.com/news/1", {"yna.co.kr"})


def test_is_allowed_link_rejects_lookalike_domain():
    # "notchosun.com"이 "chosun.com"의 서브도메인으로 오인되지 않아야 한다.
    assert not is_allowed_link("https://notchosun.com/a", {"chosun.com"})


def test_filter_allowed_articles_splits_by_domain():
    items = [
        {"title": "A", "link": "https://www.yna.co.kr/1"},
        {"title": "B", "link": "https://unknown-blog.example/2"},
    ]
    allowed, excluded = filter_allowed_articles(items)
    assert [a["title"] for a in allowed] == ["A"]
    assert [a["title"] for a in excluded] == ["B"]
