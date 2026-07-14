---
name: naver-api-client
description: 네이버 뉴스 검색 API 호출 래퍼. 요청 제한 대응(재시도/딜레이)과 응답 정규화(title/link/description/pub_date)를 담당한다.
---

# naver-api-client

## 역할
네이버 뉴스 검색 API(`GET https://openapi.naver.com/v1/search/news.json`)를 호출하고,
HTML 태그 제거·발행일 ISO 변환을 거친 정규화된 기사 목록을 반환한다.

## 트리거 조건
- 대시보드에서 "지금 업데이트" 버튼 클릭 시 (`/api/sync` → `backend/services/sync_pipeline.py`)
- 개발/디버깅 중 특정 키워드의 API 응답을 단독으로 확인하고 싶을 때 (`scripts/fetch_news.py` CLI)

## 실제 구현 위치
`backend/services/naver_client.py` — 이 스킬의 스크립트는 그 위에 얇게 얹은 CLI 래퍼다.
로직을 두 곳에 중복 구현하지 않는다.

## 사용법
```bash
python .claude/skills/naver-api-client/scripts/fetch_news.py "반도체"
python .claude/skills/naver-api-client/scripts/fetch_news.py "반도체" --display 30 --raw
```

## 제약
- `.env`의 `NAVER_CLIENT_ID` / `NAVER_CLIENT_SECRET` 필요
- 요청 사이 최소 딜레이(`NAVER_REQUEST_DELAY_SEC`) 및 재시도 횟수(`NAVER_MAX_RETRIES`)는
  `backend/config.py`에서 조정한다.
- 실패 시 `NaverApiError`를 던진다 — 호출자는 해당 키워드만 스킵하고 나머지는 계속 진행해야 한다.
