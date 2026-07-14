from backend.services.matcher import match_keywords


def test_matches_keyword_in_title():
    article = {"title": "삼성전자 반도체 실적 발표", "description": "3분기 영업이익 증가"}
    assert match_keywords(article, ["반도체", "2차전지"]) == ["반도체"]


def test_matches_keyword_in_description_case_insensitive():
    article = {"title": "Tech News", "description": "Samsung AI chip roadmap"}
    assert match_keywords(article, ["ai", "배터리"]) == ["ai"]


def test_no_match_returns_empty_list():
    article = {"title": "날씨 소식", "description": "내일은 맑음"}
    assert match_keywords(article, ["반도체"]) == []
