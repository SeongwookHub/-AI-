import hashlib
import json
from datetime import datetime, timezone

from backend.config import PIPELINE_STATE_PATH

STEPS = (
    "keyword-validated",
    "api-fetched",
    "schema-validated",
    "deduped",
    "matched",
    "saved",
)


def _hash(data) -> str:
    payload = json.dumps(data, sort_keys=True, ensure_ascii=False, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _read_state() -> dict:
    if not PIPELINE_STATE_PATH.exists():
        return {}
    with open(PIPELINE_STATE_PATH, encoding="utf-8") as f:
        return json.load(f)


def record_step(step_name: str, status: str, data=None):
    """단계 통과 여부를 _pipeline_state.json에 기록한다. 이 함수 외 직접 편집 금지."""
    if step_name not in STEPS:
        raise ValueError(f"알 수 없는 파이프라인 단계: {step_name}")
    if status not in ("pass", "fail"):
        raise ValueError(f"status는 pass/fail만 허용됩니다: {status}")

    state = _read_state()
    state[step_name] = {
        "status": status,
        "hash": _hash(data if data is not None else ""),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    PIPELINE_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(PIPELINE_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def get_state() -> dict:
    return _read_state()


def step_passed(step_name: str) -> bool:
    state = _read_state()
    entry = state.get(step_name)
    return bool(entry and entry.get("status") == "pass")
