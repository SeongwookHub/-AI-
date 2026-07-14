"""CLI 래퍼: JSON 파일(정규화된 기사 목록) 내 link 중복 여부를 검사한다.

실제 로직은 backend/services/validators.py에 있다.

사용법:
    python validate_dedup.py /tmp/normalized.json
종료 코드: 중복이 하나라도 있으면 1 (정보 제공 목적 — 실제 앱은 dedup_by_link로 자동 제거함)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from backend.services.validators import dedup_by_link  # noqa: E402


def main():
    if len(sys.argv) != 2:
        print("사용법: validate_dedup.py <json 파일>", file=sys.stderr)
        sys.exit(2)

    items = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    deduped = dedup_by_link(items)
    duplicate_count = len(items) - len(deduped)
    print(
        json.dumps(
            {"total": len(items), "unique": len(deduped), "duplicates": duplicate_count},
            ensure_ascii=False,
        )
    )
    if duplicate_count:
        sys.exit(1)


if __name__ == "__main__":
    main()
