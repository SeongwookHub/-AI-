from unittest.mock import patch

from backend.services import stock_universe

FAKE_UNIVERSE = {
    "005930": {"name": "삼성전자", "market": "KOSPI"},
    "005935": {"name": "삼성전자우", "market": "KOSPI"},
    "032830": {"name": "삼성생명", "market": "KOSPI"},
    "009150": {"name": "삼성전기", "market": "KOSPI"},
    "000660": {"name": "SK하이닉스", "market": "KOSPI"},
}


def test_search_prioritizes_names_starting_with_query():
    with patch.object(stock_universe, "get_stock_universe", return_value=FAKE_UNIVERSE):
        results = stock_universe.search_stocks("삼성")

    names = [r["name"] for r in results]
    # "삼성"으로 시작하는 종목(삼성전자/삼성전자우/삼성생명/삼성전기)이 먼저,
    # 포함만 하는 종목(SK하이닉스는 애초에 안 걸림 - 그냥 no-match 예시)은 뒤에.
    assert names == ["삼성생명", "삼성전기", "삼성전자", "삼성전자우"]


def test_search_contains_match_ranked_after_startswith_match():
    universe = {
        **FAKE_UNIVERSE,
        "999999": {"name": "한화삼성전자유사종목", "market": "KOSDAQ"},
    }
    with patch.object(stock_universe, "get_stock_universe", return_value=universe):
        results = stock_universe.search_stocks("삼성")

    names = [r["name"] for r in results]
    assert names[-1] == "한화삼성전자유사종목"
    assert names.index("삼성전자") < names.index("한화삼성전자유사종목")


def test_search_is_case_insensitive_for_english_names():
    with patch.object(stock_universe, "get_stock_universe", return_value=FAKE_UNIVERSE):
        lower = stock_universe.search_stocks("sk")
        upper = stock_universe.search_stocks("SK")
        mixed = stock_universe.search_stocks("Sk")
    assert [r["name"] for r in lower] == ["SK하이닉스"]
    assert lower == upper == mixed


def test_search_by_exact_6_digit_code():
    with patch.object(stock_universe, "get_stock_universe", return_value=FAKE_UNIVERSE):
        results = stock_universe.search_stocks("005930")
    assert results == [{"code": "005930", "name": "삼성전자", "market": "KOSPI"}]


def test_search_by_unknown_code_returns_empty():
    with patch.object(stock_universe, "get_stock_universe", return_value=FAKE_UNIVERSE):
        assert stock_universe.search_stocks("123456") == []


def test_search_no_match_returns_empty():
    with patch.object(stock_universe, "get_stock_universe", return_value=FAKE_UNIVERSE):
        assert stock_universe.search_stocks("존재안하는이상한이름") == []


def test_find_stock_by_name_exact_match_only():
    with patch.object(stock_universe, "get_stock_universe", return_value=FAKE_UNIVERSE):
        assert stock_universe.find_stock_by_name("삼성전자") == {
            "code": "005930",
            "name": "삼성전자",
            "market": "KOSPI",
        }
        assert stock_universe.find_stock_by_name("삼성") is None  # 부분일치는 등록 검증에서 불허
        assert stock_universe.find_stock_by_name("sk하이닉스") == {
            "code": "000660",
            "name": "SK하이닉스",
            "market": "KOSPI",
        }


def test_find_stock_by_code():
    with patch.object(stock_universe, "get_stock_universe", return_value=FAKE_UNIVERSE):
        assert stock_universe.find_stock_by_code("000660")["name"] == "SK하이닉스"
        assert stock_universe.find_stock_by_code("000000") is None


def test_build_stock_universe_excludes_etf_and_etn():
    kospi = {"005930": "삼성전자", "069500": "KODEX 200"}
    kosdaq = {"000660": "SK하이닉스"}
    excluded = {"069500"}  # ETF로 분류됨

    with patch.object(stock_universe, "_fetch_market_codes", side_effect=[kospi, kosdaq]), patch.object(
        stock_universe, "_fetch_excluded_codes", return_value=excluded
    ):
        universe = stock_universe.build_stock_universe()

    assert set(universe.keys()) == {"005930", "000660"}
    assert universe["005930"]["market"] == "KOSPI"
    assert universe["000660"]["market"] == "KOSDAQ"
