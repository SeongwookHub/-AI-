import json
import re
from datetime import datetime, timedelta, timezone

import requests

from backend.config import OUTPUT_DIR

UNIVERSE_CACHE_PATH = OUTPUT_DIR / "stock_universe.json"
CACHE_MAX_AGE = timedelta(hours=24)

MARKET_SUM_URL = "https://finance.naver.com/sise/sise_market_sum.naver"
ETF_LIST_URL = "https://finance.naver.com/api/sise/etfItemList.naver"
ETN_LIST_URL = "https://finance.naver.com/api/sise/etnItemList.naver"
MAX_PAGES = 80  # 안전장치 (KOSPI+KOSDAQ 실제로는 각각 50페이지 내외)

_HEADERS = {"User-Agent": "Mozilla/5.0"}
_ITEM_RE = re.compile(r'/item/main\.naver\?code=(\d{6})"[^>]*>([^<]+)</a>')
_CODE_RE = re.compile(r"\d{6}")


def _fetch_market_codes(sosok: str) -> dict[str, str]:
    codes: dict[str, str] = {}
    page = 1
    while page <= MAX_PAGES:
        response = requests.get(
            MARKET_SUM_URL, params={"sosok": sosok, "page": page}, headers=_HEADERS, timeout=10
        )
        text = response.content.decode("euc-kr", errors="replace")
        matches = _ITEM_RE.findall(text)
        if not matches:
            break
        codes.update(matches)
        page += 1
    return codes


def _fetch_excluded_codes() -> set[str]:
    """ETF/ETN은 개별 종목이 아니므로 상장 종목 목록에서 제외한다."""
    excluded: set[str] = set()
    for url, key in [(ETF_LIST_URL, "etfItemList"), (ETN_LIST_URL, "etnItemList")]:
        response = requests.get(url, headers=_HEADERS, timeout=10)
        for item in response.json()["result"][key]:
            excluded.add(item["itemcode"])
    return excluded


def build_stock_universe() -> dict[str, dict]:
    """코스피/코스닥 상장 종목(ETF/ETN 제외) 전체 목록을 네이버 금융에서 새로 수집한다."""
    kospi = _fetch_market_codes("0")
    kosdaq = _fetch_market_codes("1")
    excluded = _fetch_excluded_codes()

    universe: dict[str, dict] = {}
    for code, name in {**kospi, **kosdaq}.items():
        if code in excluded:
            continue
        universe[code] = {"name": name, "market": "KOSPI" if code in kospi else "KOSDAQ"}
    return universe


def _read_cache() -> dict | None:
    if not UNIVERSE_CACHE_PATH.exists():
        return None
    try:
        payload = json.loads(UNIVERSE_CACHE_PATH.read_text(encoding="utf-8"))
        fetched_at = datetime.fromisoformat(payload["fetched_at"])
    except (json.JSONDecodeError, KeyError, ValueError):
        return None
    if datetime.now(timezone.utc) - fetched_at > CACHE_MAX_AGE:
        return None
    return payload["stocks"]


def _write_cache(universe: dict) -> None:
    UNIVERSE_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {"fetched_at": datetime.now(timezone.utc).isoformat(), "stocks": universe}
    UNIVERSE_CACHE_PATH.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")


def get_stock_universe(force_refresh: bool = False) -> dict[str, dict]:
    """캐시가 유효하면 캐시를 쓰고, 없거나 오래됐으면(24시간) 새로 수집해 캐시에 저장한다."""
    if not force_refresh:
        cached = _read_cache()
        if cached is not None:
            return cached
    universe = build_stock_universe()
    _write_cache(universe)
    return universe


def search_stocks(query: str, limit: int = 20) -> list[dict]:
    """종목명 부분일치 또는 6자리 종목코드 완전일치로 검색한다.

    이름이 검색어로 '시작하는' 종목을 우선 정렬하고, 나머지(중간에 포함되는 것)는 뒤에 배치한다.
    """
    query = query.strip()
    if not query:
        return []

    universe = get_stock_universe()

    if _CODE_RE.fullmatch(query):
        entry = universe.get(query)
        return [{"code": query, "name": entry["name"], "market": entry["market"]}] if entry else []

    query_casefold = query.casefold()
    starts, contains = [], []
    for code, entry in universe.items():
        name = entry["name"]
        name_casefold = name.casefold()
        if query_casefold not in name_casefold:
            continue
        result = {"code": code, "name": name, "market": entry["market"]}
        (starts if name_casefold.startswith(query_casefold) else contains).append(result)

    starts.sort(key=lambda x: x["name"])
    contains.sort(key=lambda x: x["name"])
    return (starts + contains)[:limit]


def find_stock_by_name(name: str) -> dict | None:
    universe = get_stock_universe()
    name_casefold = name.casefold()
    for code, entry in universe.items():
        if entry["name"].casefold() == name_casefold:
            return {"code": code, "name": entry["name"], "market": entry["market"]}
    return None


def find_stock_by_code(code: str) -> dict | None:
    entry = get_stock_universe().get(code)
    return {"code": code, "name": entry["name"], "market": entry["market"]} if entry else None
