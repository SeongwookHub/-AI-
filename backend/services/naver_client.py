import re
import time
from email.utils import parsedate_to_datetime

import requests

from backend.config import (
    NAVER_CLIENT_ID,
    NAVER_CLIENT_SECRET,
    NAVER_MAX_RETRIES,
    NAVER_REQUEST_DELAY_SEC,
    require_naver_credentials,
)

NAVER_NEWS_API_URL = "https://openapi.naver.com/v1/search/news.json"
_TAG_RE = re.compile(r"<[^>]+>")


class NaverApiError(Exception):
    pass


def _clean_text(text: str) -> str:
    return _TAG_RE.sub("", text).replace("&quot;", '"').replace("&amp;", "&")


def _to_iso_date(pub_date: str) -> str:
    try:
        return parsedate_to_datetime(pub_date).isoformat()
    except (TypeError, ValueError):
        return pub_date


def fetch_raw(keyword: str, display: int = 100, start: int = 1) -> dict:
    """네이버 뉴스 검색 API 원시 응답(JSON)을 반환한다. 실패 시 재시도 후 NaverApiError."""
    require_naver_credentials()
    headers = {
        "X-Naver-Client-Id": NAVER_CLIENT_ID,
        "X-Naver-Client-Secret": NAVER_CLIENT_SECRET,
    }
    params = {"query": keyword, "display": display, "sort": "date", "start": start}

    last_error: Exception | None = None
    for attempt in range(NAVER_MAX_RETRIES + 1):
        try:
            response = requests.get(
                NAVER_NEWS_API_URL, headers=headers, params=params, timeout=10
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            last_error = e
            if attempt < NAVER_MAX_RETRIES:
                time.sleep(NAVER_REQUEST_DELAY_SEC * (attempt + 1))
    raise NaverApiError(f"'{keyword}' 뉴스 수집 실패: {last_error}")


def fetch_raw_pages(keyword: str, pages: int = 3, display: int = 100) -> list[dict]:
    """여러 페이지(start=1,101,201...)를 순차 호출해 원시 응답 목록을 반환한다.

    인기 종목은 최신 100건이 전부 1시간 이내에 몰릴 정도로 뉴스량이 많아, 한 페이지만
    가져오면 '오늘'/'어제 이전' 구간이 항상 비어 보인다. 조금 더 과거까지 확보하기 위해
    기본 3페이지(최대 300건)를 순차 호출한다. 네이버 검색 API의 start 상한(1000)을 넘지 않는다.
    """
    raw_payloads = []
    for page in range(pages):
        start = page * display + 1
        if start > 1000:
            break
        if page > 0:
            time.sleep(NAVER_REQUEST_DELAY_SEC)
        raw_payloads.append(fetch_raw(keyword, display=display, start=start))
    return raw_payloads


def normalize_items(raw_payload: dict) -> list[dict]:
    """원시 API 응답을 구조화 JSON(스키마: title/link/description/pub_date)으로 변환."""
    items = []
    for item in raw_payload.get("items", []):
        items.append(
            {
                "title": _clean_text(item.get("title", "")),
                "link": item.get("originallink") or item.get("link", ""),
                "description": _clean_text(item.get("description", "")),
                "pub_date": _to_iso_date(item.get("pubDate", "")),
            }
        )
    return items


def fetch_news_for_keyword(keyword: str, display: int = 100) -> list[dict]:
    """원시 호출 + 정규화를 한 번에 수행하는 편의 함수(스킬 CLI 등에서 사용)."""
    return normalize_items(fetch_raw(keyword, display))
