"""CLI 래퍼: 기사(JSON)와 키워드 목록을 받아 매칭되는 키워드를 출력한다.

실제 로직은 backend/services/matcher.py에 있다.

사용법:
    echo '{"title": "삼성전자 반도체 실적", "description": "..."}' | \
        python match_keywords.py --keywords 반도체 삼성전자
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from backend.services.matcher import match_keywords  # noqa: E402


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--keywords", nargs="+", required=True)
    args = parser.parse_args()

    article = json.load(sys.stdin)
    matched = match_keywords(article, args.keywords)
    print(json.dumps({"matched": matched}, ensure_ascii=False))


if __name__ == "__main__":
    main()
