"""CLI 래퍼: 정규화된 기사 JSON(title/link/description/pub_date)의 필수 필드 존재 여부를 검증한다.

주의: 이 검증은 "구조화 JSON 생성" 이후 단계에 적용된다. output/_raw/*.json은
네이버 API 원시 응답(필드명이 pubDate 등으로 다름)이므로 이 스크립트의 대상이 아니다.
원시 응답을 구조화 JSON으로 변환하려면 naver-api-client 스킬의 fetch_news.py(--raw 옵션 없이)를 사용한다.

실제 로직은 backend/services/validators.py에 있다.

사용법:
    python fetch_news.py "반도체" > /tmp/normalized.json
    python validate_article_schema.py /tmp/normalized.json
종료 코드: invalid 항목이 하나라도 있으면 1 (경고 목적, 앱 동작 자체를 막지 않음)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from backend.services.validators import validate_article_schema  # noqa: E402


def main():
    if len(sys.argv) != 2:
        print("사용법: validate_article_schema.py <json 파일>", file=sys.stderr)
        sys.exit(2)

    path = Path(sys.argv[1])
    payload = json.loads(path.read_text(encoding="utf-8"))
    items = payload.get("items", payload) if isinstance(payload, dict) else payload

    valid, invalid = validate_article_schema(items)
    print(
        json.dumps(
            {"valid_count": len(valid), "invalid_count": len(invalid)},
            ensure_ascii=False,
        )
    )
    if invalid:
        print(f"[FAIL] 필수 필드 누락 항목 {len(invalid)}건", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
