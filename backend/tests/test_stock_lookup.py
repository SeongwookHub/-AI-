from unittest.mock import patch

from backend.services.stock_lookup import chart_image_url, get_stock_snapshot, item_page_url

SNAPSHOT_RESPONSE = {
    "datas": [
        {
            "closePrice": "263,000",
            "compareToPreviousClosePrice": "8,500",
            "fluctuationsRatio": "3.34",
            "compareToPreviousPrice": {"name": "RISING"},
            "marketStatus": "OPEN",
            "openPrice": "255,000",
            "highPrice": "270,000",
            "lowPrice": "247,000",
            "accumulatedTradingVolume": "35,054,797",
        }
    ]
}


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_get_stock_snapshot_parses_fields():
    with patch("requests.get", return_value=FakeResponse(SNAPSHOT_RESPONSE)):
        snapshot = get_stock_snapshot("005930")
    assert snapshot == {
        "price": "263,000",
        "change": "8,500",
        "change_ratio": "3.34",
        "direction": "RISING",
        "market_status": "OPEN",
        "open_price": "255,000",
        "high_price": "270,000",
        "low_price": "247,000",
        "volume": "35,054,797",
    }


def test_get_stock_snapshot_returns_none_when_empty():
    with patch("requests.get", return_value=FakeResponse({"datas": []})):
        assert get_stock_snapshot("005930") is None


def test_chart_image_url_format():
    assert (
        chart_image_url("005930")
        == "https://ssl.pstatic.net/imgfinance/chart/item/area/day/005930.png"
    )


def test_item_page_url_format():
    assert item_page_url("005930") == "https://finance.naver.com/item/main.naver?code=005930"
