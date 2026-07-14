import re

import requests

RESEARCH_LIST_URL = "https://finance.naver.com/research/company_list.naver"
_HEADERS = {"User-Agent": "Mozilla/5.0"}

_ROW_RE = re.compile(r"<tr>(.*?)</tr>", re.S)
_TITLE_RE = re.compile(r'<a href="(company_read\.naver\?[^"]+)"[^>]*>([^<]+)</a>')
_BROKER_RE = re.compile(r"</a>\s*</td>\s*<td>([^<]+)</td>")
_PDF_RE = re.compile(r'<a href="(https://stock\.pstatic\.net/stock-research/[^"]+\.pdf)"')
_DATE_RE = re.compile(r'<td class="date"[^>]*>([\d.]+)</td>')


def get_research_reports(code: str, limit: int = 5) -> list[dict]:
    """종목별 최근 증권사 리포트 목록을 스크래핑한다. 실패하면 빈 리스트를 반환한다."""
    try:
        response = requests.get(
            RESEARCH_LIST_URL,
            params={"searchType": "itemCode", "itemCode": code},
            headers=_HEADERS,
            timeout=10,
        )
        response.raise_for_status()
        html = response.content.decode("euc-kr", errors="replace")
    except requests.RequestException:
        return []

    reports = []
    for row in _ROW_RE.findall(html):
        title_match = _TITLE_RE.search(row)
        if not title_match:
            continue

        broker_match = _BROKER_RE.search(row)
        pdf_match = _PDF_RE.search(row)
        date_match = _DATE_RE.search(row)

        reports.append(
            {
                "title": title_match.group(2).strip(),
                "detail_url": f"https://finance.naver.com/research/{title_match.group(1)}",
                "broker": broker_match.group(1).strip() if broker_match else "",
                "date": date_match.group(1) if date_match else "",
                "pdf_url": pdf_match.group(1) if pdf_match else None,
            }
        )
        if len(reports) >= limit:
            break

    return reports
