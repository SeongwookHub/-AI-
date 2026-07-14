"""CLI 래퍼: 네이버 뉴스 검색 API를 호출해 정규화된 JSON을 stdout에 출력한다.

실제 로직은 backend/services/naver_client.py에 있다(단일 소스 유지, 중복 구현 금지).

사용법:
    python fetch_news.py "<키워드>" [--display N] [--raw]
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from backend.services.naver_client import NaverApiError, fetch_raw, normalize_items  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("keyword")
    parser.add_argument("--display", type=int, default=100)
    parser.add_argument("--raw", action="store_true", help="정규화하지 않은 원시 응답 출력")
    args = parser.parse_args()

    try:
        raw = fetch_raw(args.keyword, args.display)
    except NaverApiError as e:
        print(json.dumps({"error": str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    output = raw if args.raw else normalize_items(raw)
    print(json.dumps(output, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
