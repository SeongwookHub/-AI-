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


def test_get_stock_snapshot_parses_krx_fields_and_defaults_nxt_to_none():
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
        "nxt_price": None,
        "nxt_change": None,
        "nxt_change_ratio": None,
        "nxt_direction": None,
        "market_status_label": "장중",
    }


def test_get_stock_snapshot_parses_nxt_fields_when_present():
    response = {
        "datas": [
            {
                **SNAPSHOT_RESPONSE["datas"][0],
                "marketStatus": "CLOSE",
                "overMarketPriceInfo": {
                    "overMarketStatus": "OPEN",
                    "overPrice": "267,000",
                    "compareToPreviousClosePrice": "12,500",
                    "fluctuationsRatio": "4.91",
                    "compareToPreviousPrice": {"name": "RISING"},
                },
            }
        ]
    }
    with patch("requests.get", return_value=FakeResponse(response)):
        snapshot = get_stock_snapshot("005930")
    assert snapshot["nxt_price"] == "267,000"
    assert snapshot["nxt_change"] == "12,500"
    assert snapshot["nxt_change_ratio"] == "4.91"
    assert snapshot["nxt_direction"] == "RISING"
    assert snapshot["market_status_label"] == "시간외"


def test_market_status_label_falls_back_to_closed():
    response = {
        "datas": [{**SNAPSHOT_RESPONSE["datas"][0], "marketStatus": "CLOSE"}]
    }
    with patch("requests.get", return_value=FakeResponse(response)):
        snapshot = get_stock_snapshot("005930")
    assert snapshot["market_status_label"] == "장마감"


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
