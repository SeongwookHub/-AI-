import requests

AUTOCOMPLETE_URL = "https://ac.stock.naver.com/ac"
SNAPSHOT_URL_TEMPLATE = "https://polling.finance.naver.com/api/realtime/domestic/stock/{code}"
CHART_IMAGE_URL_TEMPLATE = "https://ssl.pstatic.net/imgfinance/chart/item/area/day/{code}.png"

# 네이버가 공식 문서화하지 않은 내부 엔드포인트라 User-Agent 없이는 차단될 수 있다.
_HEADERS = {"User-Agent": "Mozilla/5.0"}


def resolve_stock_code(query: str) -> dict | None:
    """종목명으로 네이버 증권 자동완성 API를 조회해 정확히 일치하는 종목을 찾는다.

    ETF 등 이름에 검색어가 포함될 뿐인 상품과 혼동하지 않도록, 이름이 완전히
    일치하는 종목만 반환한다. 못 찾으면 None (일반 키워드로만 취급).
    """
    try:
        response = requests.get(
            AUTOCOMPLETE_URL,
            params={"q": query, "target": "stock,index,futures"},
            headers=_HEADERS,
            timeout=5,
        )
        response.raise_for_status()
        data = response.json()
    except (requests.RequestException, ValueError):
        return None

    for item in data.get("items", []):
        if item.get("category") == "stock" and item.get("name") == query:
            return {
                "code": item["code"],
                "name": item["name"],
                "market": item.get("typeCode", ""),
            }
    return None


def get_stock_snapshot(code: str) -> dict | None:
    """현재가/전일대비 등 실시간 시세 스냅샷을 조회한다. 실패 시 None."""
    try:
        response = requests.get(
            SNAPSHOT_URL_TEMPLATE.format(code=code), headers=_HEADERS, timeout=5
        )
        response.raise_for_status()
        datas = response.json().get("datas", [])
    except (requests.RequestException, ValueError):
        return None

    if not datas:
        return None

    item = datas[0]
    return {
        "price": item.get("closePrice"),
        "change": item.get("compareToPreviousClosePrice"),
        "change_ratio": item.get("fluctuationsRatio"),
        "direction": item.get("compareToPreviousPrice", {}).get("name"),  # RISING/FALLING/UNCHANGED
        "market_status": item.get("marketStatus"),
    }


def chart_image_url(code: str) -> str:
    return CHART_IMAGE_URL_TEMPLATE.format(code=code)
