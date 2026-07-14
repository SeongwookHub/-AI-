---
name: schema-validator
description: 키워드 입력값, 구조화된 기사 JSON의 필수 필드, link 기준 중복 여부를 검증하는 게이트 로직 모음.
---

# schema-validator

## 역할
동기화 파이프라인의 각 단계가 다음 단계로 넘어가기 전 통과해야 하는 검증 3종을 제공한다.

| 스크립트 | 검증 대상 | 실제 로직 |
|---|---|---|
| `validate_keywords.py` | 신규 키워드(빈 값/중복) | `backend/services/validators.validate_keyword_input` |
| `validate_article_schema.py` | 구조화된 기사의 필수 필드(title/link/pub_date) | `backend/services/validators.validate_article_schema` |
| `validate_dedup.py` | 기사 목록의 link 유일성 | `backend/services/validators.dedup_by_link` |

## 트리거 조건
- 키워드 추가 요청 시 (`POST /api/keywords`)
- 네이버 API 응답을 구조화 JSON으로 변환한 직후, 저장 직전 (`sync_pipeline.py`)
- `.claude/hooks/gate_dispatch.py`가 관련 파일 변경을 감지했을 때 (4장 하네스 스펙 참고)

## 실패 처리 원칙
- 키워드 검증 실패 → 저장 거부, 에러 메시지 반환 (앱 동작을 막음)
- 기사 스키마/dedup 검증 실패 → 해당 항목만 제외하고 나머지는 계속 진행 (전체 동기화를 막지 않음)
  CLI 스크립트의 비정상 종료 코드는 어디까지나 개발/훅 단계의 경고 신호이며,
  런타임 앱은 `validators.py`의 함수 반환값(제외 리스트)으로 직접 판단한다.

## 사용법
```bash
python .claude/skills/schema-validator/scripts/validate_keywords.py "반도체"
python .claude/skills/schema-validator/scripts/validate_article_schema.py /tmp/normalized.json
python .claude/skills/schema-validator/scripts/validate_dedup.py /tmp/normalized.json
```
