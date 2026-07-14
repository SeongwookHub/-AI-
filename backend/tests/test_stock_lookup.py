from unittest.mock import patch

import requests

from backend.services.stock_lookup import (
    chart_image_url,
    get_stock_snapshot,
    resolve_stock_code,
)

AUTOCOMPLETE_RESPONSE = {
    "query": "삼성전자",
    "items": [
        {"code": "005930", "name": "삼성전자", "typeCode": "KOSPI", "category": "stock"},
        {
            "code": "0193W0",
            "name": "KODEX 삼성전자단일종목레버리지",
            "typeCode": "KOSPI",
            "category": "stock",
        },
    ],
}

SNAPSHOT_RESPONSE = {
    "datas": [
        {
            "closePrice": "263,000",
            "compareToPreviousClosePrice": "8,500",
            "fluctuationsRatio": "3.34",
            "compareToPreviousPrice": {"name": "RISING"},
            "marketStatus": "OPEN",
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


def test_resolve_stock_code_picks_exact_name_match():
    with patch("requests.get", return_value=FakeResponse(AUTOCOMPLETE_RESPONSE)):
        result = resolve_stock_code("삼성전자")
    assert result == {"code": "005930", "name": "삼성전자", "market": "KOSPI"}


def test_resolve_stock_code_returns_none_for_non_stock_keyword():
    with patch("requests.get", return_value=FakeResponse({"items": []})):
        assert resolve_stock_code("아무거나키워드") is None


def test_resolve_stock_code_returns_none_on_network_error():
    with patch("requests.get", side_effect=requests.RequestException("boom")):
        assert resolve_stock_code("삼성전자") is None


def test_get_stock_snapshot_parses_fields():
    with patch("requests.get", return_value=FakeResponse(SNAPSHOT_RESPONSE)):
        snapshot = get_stock_snapshot("005930")
    assert snapshot == {
        "price": "263,000",
        "change": "8,500",
        "change_ratio": "3.34",
        "direction": "RISING",
        "market_status": "OPEN",
    }


def test_get_stock_snapshot_returns_none_when_empty():
    with patch("requests.get", return_value=FakeResponse({"datas": []})):
        assert get_stock_snapshot("005930") is None


def test_chart_image_url_format():
    assert (
        chart_image_url("005930")
        == "https://ssl.pstatic.net/imgfinance/chart/item/area/day/005930.png"
    )
