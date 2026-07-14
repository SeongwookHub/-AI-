"""CLI 래퍼: 신규 키워드 문자열이 빈 값이 아니고 중복되지 않는지 검증한다.

실제 로직은 backend/services/validators.py에 있다. 현재 등록된 키워드 목록은
backend/services/storage.py(SQLite, output/articles.db)에서 조회한다.

사용법:
    python validate_keywords.py "반도체"
종료 코드: 검증 실패 시 1
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from backend.services import storage  # noqa: E402
from backend.services.validators import validate_keyword_input  # noqa: E402


def main():
    if len(sys.argv) != 2:
        print("사용법: validate_keywords.py <키워드>", file=sys.stderr)
        sys.exit(2)

    storage.init_db()
    existing = [k["keyword"] for k in storage.list_keywords()]
    ok, error = validate_keyword_input(sys.argv[1], existing)
    print(json.dumps({"ok": ok, "error": error}, ensure_ascii=False))
    if not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
