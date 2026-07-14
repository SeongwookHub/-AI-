"""PostToolUse 훅 디스패처.

Claude Code가 Edit/Write/MultiEdit로 파일을 수정할 때마다 호출된다(.claude/settings.json 참고).
stdin으로 받은 tool_input.file_path를 보고 관련된 검증 스크립트만 골라서 실행한다.

주의: 이 저장소는 키워드/기사 저장소로 SQLite(output/articles.db)를 쓰기 때문에,
설계서 4.1의 "keywords.json 수정" / "articles.* 수정" 트리거는 여기서는 적용 대상이 없다
(SQLite 파일은 Claude Code의 Edit/Write 대상이 아니며, 키워드 검증은
backend/routes/keywords.py에서 validate_keyword_input으로 항상 인라인 수행된다).
실제로 의미 있게 작동하는 트리거는 아래 두 가지뿐이다:
  1. backend/**/*.py 변경 → 단위 테스트 실행
  2. output/_raw/*.json 변경(테스트 픽스처 등) → 원시 응답 최소 스키마 확인
"""
import json
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def check_raw_json(file_path: Path) -> tuple[bool, str]:
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        return False, f"JSON 파싱 실패: {e}"
    if not isinstance(payload, dict) or "items" not in payload:
        return False, "네이버 API 원시 응답 형식이 아닙니다 ('items' 키 없음)."
    return True, ""


def run_backend_tests() -> tuple[bool, str]:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "backend/tests", "-q"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    return result.returncode == 0, (result.stdout + result.stderr)[-2000:]


def main():
    try:
        payload = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(0)  # 훅 입력이 없으면 조용히 통과

    file_path = payload.get("tool_input", {}).get("file_path")
    if not file_path:
        sys.exit(0)

    path = Path(file_path)
    try:
        rel = path.resolve().relative_to(PROJECT_ROOT)
    except ValueError:
        sys.exit(0)
    rel_str = str(rel).replace("\\", "/")

    if rel_str.startswith("backend/") and rel_str.endswith(".py"):
        ok, detail = run_backend_tests()
        if not ok:
            print(f"[gate] backend 테스트 실패:\n{detail}", file=sys.stderr)
            sys.exit(1)
        print("[gate] backend 테스트 통과")
        return

    if rel_str.startswith("output/_raw/") and rel_str.endswith(".json"):
        ok, detail = check_raw_json(path)
        if not ok:
            print(f"[gate] 원시 응답 스키마 확인 실패: {detail}", file=sys.stderr)
            sys.exit(1)
        print("[gate] 원시 응답 스키마 확인 통과")
        return

    sys.exit(0)


if __name__ == "__main__":
    main()
