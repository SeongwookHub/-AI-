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
    market_status = item.get("marketStatus")
    over_market = item.get("overMarketPriceInfo") or {}
    over_status = over_market.get("overMarketStatus")

    return {
        # KRX(정규장) 시세 - 기존 필드, 이름 유지(프런트 하위호환)
        "price": item.get("closePrice"),
        "change": item.get("compareToPreviousClosePrice"),
        "change_ratio": item.get("fluctuationsRatio"),
        "direction": item.get("compareToPreviousPrice", {}).get("name"),  # RISING/FALLING/UNCHANGED
        "market_status": market_status,
        "open_price": item.get("openPrice"),
        "high_price": item.get("highPrice"),
        "low_price": item.get("lowPrice"),
        "volume": item.get("accumulatedTradingVolume"),
        # NXT(넥스트레이드) 시세 - overMarketPriceInfo가 없으면 전부 None
        "nxt_price": over_market.get("overPrice"),
        "nxt_change": over_market.get("compareToPreviousClosePrice"),
        "nxt_change_ratio": over_market.get("fluctuationsRatio"),
        "nxt_direction": over_market.get("compareToPreviousPrice", {}).get("name"),
        "market_status_label": _market_status_label(market_status, over_status),
    }


def _market_status_label(market_status: str | None, over_status: str | None) -> str:
    """장중/시간외/장마감 중 하나로 사람이 읽기 쉬운 상태 라벨을 계산한다."""
    if market_status == "OPEN":
        return "장중"
    if over_status == "OPEN":
        return "시간외"
    return "장마감"


def chart_image_url(code: str) -> str:
    return CHART_IMAGE_URL_TEMPLATE.format(code=code)


def item_page_url(code: str) -> str:
    """차트를 누르면 이동할, 네이버 증권의 해당 종목 상세 페이지 주소."""
    return ITEM_PAGE_URL_TEMPLATE.format(code=code)
