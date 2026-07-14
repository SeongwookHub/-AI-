from unittest.mock import patch

import requests

from backend.services.research_reports import get_research_reports

SAMPLE_HTML = """
<table>
<tr>
    <td style="padding-left:10">
        <a href="/item/main.naver?code=005930" title="삼성전자" class="stock_item">삼성전자</a>
    </td>
    <td><a href="company_read.naver?nid=93968&page=1&searchType=itemCode&itemCode=005930">실적 전망치 상향 조정 지속</a></td>
    <td>iM증권</td>
    <td class="file">
        <a href="https://stock.pstatic.net/stock-research/company/61/20260708_company_427704000.pdf" target="_blank"><img src="https://ssl.pstatic.net/imgstock/images5/down.gif" alt="pdf" align="absmiddle"></a>
    </td>
    <td class="date" style="padding-left:5px">26.07.08</td>
    <td class="date">23483</td>
</tr>
<tr>
    <td style="padding-left:10">
        <a href="/item/main.naver?code=005930" title="삼성전자" class="stock_item">삼성전자</a>
    </td>
    <td><a href="company_read.naver?nid=93900&page=1&searchType=itemCode&itemCode=005930">2분기 실적 프리뷰</a></td>
    <td>한국투자증권</td>
    <td class="file"></td>
    <td class="date" style="padding-left:5px">26.07.01</td>
    <td class="date">18200</td>
</tr>
</table>
"""


class FakeResponse:
    def __init__(self, content: bytes):
        self.content = content

    def raise_for_status(self):
        pass


def test_get_research_reports_parses_rows():
    with patch("requests.get", return_value=FakeResponse(SAMPLE_HTML.encode("euc-kr"))):
        reports = get_research_reports("005930")

    assert len(reports) == 2
    first = reports[0]
    assert first["title"] == "실적 전망치 상향 조정 지속"
    assert first["broker"] == "iM증권"
    assert first["date"] == "26.07.08"
    assert first["pdf_url"] == (
        "https://stock.pstatic.net/stock-research/company/61/20260708_company_427704000.pdf"
    )
    assert first["detail_url"].startswith("https://finance.naver.com/research/company_read.naver?")

    second = reports[1]
    assert second["title"] == "2분기 실적 프리뷰"
    assert second["broker"] == "한국투자증권"
    assert second["pdf_url"] is None  # 파일 링크 없는 리포트도 있음


def test_get_research_reports_respects_limit():
    with patch("requests.get", return_value=FakeResponse(SAMPLE_HTML.encode("euc-kr"))):
        reports = get_research_reports("005930", limit=1)
    assert len(reports) == 1


def test_get_research_reports_returns_empty_on_network_error():
    with patch("requests.get", side_effect=requests.RequestException("boom")):
        assert get_research_reports("005930") == []


def test_get_research_reports_returns_empty_when_no_rows_match():
    with patch("requests.get", return_value=FakeResponse("<table></table>".encode("euc-kr"))):
        assert get_research_reports("005930") == []
