from unittest.mock import patch

from backend.services.naver_client import fetch_raw_pages


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def test_fetch_raw_pages_uses_increasing_start_offsets():
    calls = []

    def fake_get(url, headers, params, timeout):
        calls.append(params.copy())
        return FakeResponse({"items": [{"title": f"item at start={params['start']}"}]})

    with patch("requests.get", side_effect=fake_get):
        pages = fetch_raw_pages("삼성전자", pages=3, display=100)

    assert len(pages) == 3
    assert [c["start"] for c in calls] == [1, 101, 201]
    assert all(c["display"] == 100 for c in calls)


def test_fetch_raw_pages_stops_before_naver_start_limit():
    calls = []

    def fake_get(url, headers, params, timeout):
        calls.append(params.copy())
        return FakeResponse({"items": []})

    # display=500이면 두 번째 페이지의 start가 이미 501 -> 세 번째 페이지는 1001로 상한 초과, 호출 안 함
    with patch("requests.get", side_effect=fake_get):
        pages = fetch_raw_pages("삼성전자", pages=3, display=500)

    assert [c["start"] for c in calls] == [1, 501]
    assert len(pages) == 2
