import json
from datetime import datetime, timezone

from backend.config import RAW_DIR
from backend.services import pipeline_state, storage
from backend.services.matcher import match_keywords
from backend.services.naver_client import NaverApiError, fetch_raw_pages, normalize_items
from backend.services.press_registry import filter_allowed_articles, get_allowed_domains, is_allowed_link
from backend.services.validators import dedup_by_link, validate_article_schema


def _save_raw(keyword: str, raw_payload: dict, page: int = 0) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
    safe_keyword = "".join(c if c.isalnum() else "_" for c in keyword)
    path = RAW_DIR / f"{safe_keyword}_p{page}_{timestamp}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(raw_payload, f, ensure_ascii=False, indent=2)


def sync_all_keywords() -> dict:
    """전체 동기화 파이프라인 실행.

    흐름: 키워드 목록 로드 → 키워드별 API 호출 → 구조화 → 허용 언론사 필터링
          → 스키마 검증 → 중복 제거 → 키워드 매칭 → upsert 저장 → pipeline_state 기록

    "허용 언론사 필터링": backend/press_outlets.json에 등록된 섹터별 주요 언론사
    도메인에 속하지 않는 기사는 전체 파이프라인에서 제외한다 (전 언론사 수집 금지).

    Returns: {"synced_at", "per_keyword_new_count", "failed_keywords"}
    """
    keyword_rows = storage.list_keywords()
    all_keyword_names = [row["keyword"] for row in keyword_rows]

    per_keyword_new_count: dict[str, int] = {}
    failed_keywords: list[str] = []

    all_valid_items: list[dict] = []
    all_invalid_items: list[dict] = []
    total_excluded_by_outlet = 0
    fetched_ok = False

    for row in keyword_rows:
        keyword = row["keyword"]
        try:
            raw_pages = fetch_raw_pages(keyword)
        except NaverApiError:
            failed_keywords.append(keyword)
            continue

        fetched_ok = True
        items = []
        for page, raw_payload in enumerate(raw_pages):
            _save_raw(keyword, raw_payload, page)
            items.extend(normalize_items(raw_payload))

        items, excluded_by_outlet = filter_allowed_articles(items)
        total_excluded_by_outlet += len(excluded_by_outlet)

        valid_items, invalid_items = validate_article_schema(items)
        all_valid_items.extend(valid_items)
        all_invalid_items.extend(invalid_items)

        deduped_items = dedup_by_link(valid_items)

        new_count = 0
        for item in deduped_items:
            matched = match_keywords(item, all_keyword_names)
            # 매칭되는 키워드가 없으면 태그 없이 저장 → "미분류"로 분류됨 (storage.list_unclassified_articles)
            matched_ids = [r["id"] for r in keyword_rows if r["keyword"] in matched]
            is_new = storage.upsert_article(item, matched_ids)
            if is_new:
                new_count += 1
        per_keyword_new_count[keyword] = new_count

    pipeline_state.record_step(
        "api-fetched", "pass" if fetched_ok else "fail", data=list(per_keyword_new_count)
    )
    pipeline_state.record_step(
        "schema-validated",
        "pass" if not all_invalid_items else "fail",
        data={
            "valid": len(all_valid_items),
            "invalid": len(all_invalid_items),
            "excluded_by_outlet": total_excluded_by_outlet,
        },
    )
    pipeline_state.record_step("deduped", "pass", data=len(all_valid_items))
    pipeline_state.record_step("matched", "pass", data=all_keyword_names)
    pipeline_state.record_step(
        "saved", "pass", data=per_keyword_new_count
    )

    synced_at = datetime.now(timezone.utc).isoformat()
    storage.set_meta("last_sync_at", synced_at)

    return {
        "synced_at": synced_at,
        "per_keyword_new_count": per_keyword_new_count,
        "failed_keywords": failed_keywords,
        "excluded_by_outlet": total_excluded_by_outlet,
    }


def purge_disallowed_articles() -> int:
    """backend/press_outlets.json 허용 목록에 없는 언론사의 기존 저장 기사를 정리한다.

    허용 언론사 필터링은 신규 수집 시점부터만 적용되므로, 목록을 바꾼 뒤
    이미 저장된 예전 기사를 함께 정리하고 싶을 때 호출한다.
    """
    allowed_domains = get_allowed_domains()
    to_delete = [
        a["id"]
        for a in storage.list_all_articles()
        if not is_allowed_link(a["link"], allowed_domains)
    ]
    return storage.delete_articles(to_delete)
