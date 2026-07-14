import requests

SNAPSHOT_URL_TEMPLATE = "https://polling.finance.naver.com/api/realtime/domestic/stock/{code}"
CHART_IMAGE_URL_TEMPLATE = "https://ssl.pstatic.net/imgfinance/chart/item/area/day/{code}.png"
ITEM_PAGE_URL_TEMPLATE = "https://finance.naver.com/item/main.naver?code={code}"

# 네이버가 공식 문서화하지 않은 내부 엔드포인트라 User-Agent 없이는 차단될 수 있다.
_HEADERS = {"User-Agent": "Mozilla/5.0"}


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
        "open_price": item.get("openPrice"),
        "high_price": item.get("highPrice"),
        "low_price": item.get("lowPrice"),
        "volume": item.get("accumulatedTradingVolume"),
    }


def chart_image_url(code: str) -> str:
    return CHART_IMAGE_URL_TEMPLATE.format(code=code)


def item_page_url(code: str) -> str:
    """차트를 누르면 이동할, 네이버 증권의 해당 종목 상세 페이지 주소."""
    return ITEM_PAGE_URL_TEMPLATE.format(code=code)
