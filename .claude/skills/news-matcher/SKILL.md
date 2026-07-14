---
name: news-matcher
description: 기사 제목/설명에 등록된 키워드 문자열이 포함되는지 판정하는 단순 포함 매칭 로직. 매칭되는 키워드가 없으면 해당 기사는 "미분류"로 남는다.
---

# news-matcher

## 역할
기사의 title/description에 각 키워드 문자열이 (대소문자 무시) 포함되는지 검사해
매칭되는 키워드 목록을 반환한다. 판단이 아니라 결정론적 문자열 포함 검사이므로
런타임에 LLM을 호출하지 않는다.

## 트리거 조건
신규 기사를 저장하기 직전, 동기화 파이프라인(`backend/services/sync_pipeline.py`)에서
등록된 전체 키워드에 대해 실행된다. 검색에 사용한 키워드 하나만이 아니라
현재 등록된 모든 키워드를 기준으로 재검사하므로, 한 기사가 여러 키워드에 동시에 태깅될 수 있다.

## 실제 구현 위치
`backend/services/matcher.py` (`match_keywords(article, keywords)`)

## 미매칭 처리
매칭되는 키워드가 하나도 없으면 해당 기사는 어떤 키워드에도 태깅되지 않고
대시보드의 "미분류" 탭(`GET /api/articles` — keyword_id 미지정)에 노출된다.

## 사용법
```bash
echo '{"title": "삼성전자 반도체 실적 발표", "description": "..."}' | \
    python .claude/skills/news-matcher/scripts/match_keywords.py --keywords 반도체 삼성전자 2차전지
```
