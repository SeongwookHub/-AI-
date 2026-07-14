# 네이버 뉴스 키워드 대시보드

## 프로젝트 개요 및 목적
사용자가 지정한 키워드를 기준으로 네이버 뉴스를 수집·분류해서 보여주는 로컬 대시보드.
"지금 업데이트" 버튼을 누르면 네이버 뉴스 검색 API로 최신 기사를 가져와 동기화한다.
설계 배경과 워크플로우 전체는 [naver-news-dashboard-design.md](naver-news-dashboard-design.md)를 참고한다.
이 문서(CLAUDE.md)는 실제 구현이 설계서와 달라진 지점(특히 저장소를 SQLite로 선택한 부분)을 포함해
"지금 코드가 실제로 어떻게 동작하는지"를 설명한다.

## 폴더 구조
```
backend/
  main.py              # FastAPI 앱, 라우터 등록 + frontend 정적 서빙
  config.py            # .env 로딩, 경로 상수
  routes/               # keywords.py, sync.py, articles.py
  services/
    naver_client.py     # 네이버 API 호출 + 정규화 (원 소스)
    matcher.py          # 키워드 포함 매칭 (원 소스)
    validators.py        # 키워드/스키마/dedup 검증 (원 소스)
    storage.py           # SQLite CRUD (keywords/articles/article_keywords/meta)
    sync_pipeline.py      # 전체 동기화 오케스트레이션
    pipeline_state.py     # output/_pipeline_state.json 기록
  tests/                # pytest 단위 테스트
frontend/               # 정적 HTML/JS/CSS (빌드 도구 없음)
output/
  articles.db           # SQLite (gitignore)
  _raw/                 # 네이버 API 원시 응답 아카이브 (gitignore)
  _pipeline_state.json   # 파이프라인 단계별 통과 기록 (gitignore, 스크립트만 기록)
.claude/
  settings.json         # PostToolUse 훅 설정
  hooks/gate_dispatch.py # 훅 디스패처
  skills/
    naver-api-client/    # backend/services/naver_client.py의 CLI 래퍼
    news-matcher/        # backend/services/matcher.py의 CLI 래퍼
    schema-validator/     # backend/services/validators.py의 CLI 래퍼
```

## 설계서와 다른 점 (중요)
설계서(3.9)는 저장소를 `keywords.json` / `articles.json`으로 예시했지만,
실제 구현은 **SQLite**(`output/articles.db`)로 확정했다 (사용자 확인 완료).
따라서:
- 키워드는 `keywords` 테이블, 기사는 `articles` 테이블 + `article_keywords` 다대다 연결 테이블로 저장한다.
  (한 기사가 여러 키워드에 동시에 매칭될 수 있으므로 다대다 구조가 필요하다.)
- 설계서 4.1의 "keywords.json 수정 / articles.* 수정" 훅 트리거는 여기서는 적용 대상이 없다.
  SQLite 파일은 Claude Code의 Edit/Write 대상이 아니기 때문이다. 대신 키워드 검증은
  `backend/routes/keywords.py`에서 `validate_keyword_input`으로 **항상 인라인 수행**된다.
  실제로 파일 변경 기반으로 작동하는 훅은 `backend/**/*.py`(단위 테스트 실행)와
  `output/_raw/*.json`(원시 응답 최소 스키마 확인) 두 가지뿐이다. 자세한 내용은
  `.claude/hooks/gate_dispatch.py` 상단 주석 참고.

## 언론사 화이트리스트 필터링
전체 언론사의 뉴스를 다 수집하지 않고, 섹터(정치/경제/사회/생활문화/IT과학/세계)별 주요 언론사
5곳씩으로 구성된 화이트리스트에 속한 기사만 저장한다 (사용자 요청으로 추가된 기능).
- 목록: `backend/press_outlets.json` — 직접 편집해서 언론사를 추가/제거할 수 있다.
  네이버 검색 API는 언론사 조회수·섹터 분류 데이터를 제공하지 않으므로, 이 목록은
  실시간 랭킹이 아니라 Claude가 제안한 정적 기본값이다.
- 필터 로직: `backend/services/press_registry.py` (`is_allowed_link`, `filter_allowed_articles`)
  — 기사 링크의 호스트명이 화이트리스트 도메인과 일치하거나 그 서브도메인일 때만 통과.
- 적용 시점: `sync_pipeline.sync_all_keywords()`에서 정규화 직후, 스키마 검증 이전에 필터링한다.
  걸러진 기사 수는 `/api/sync` 응답의 `excluded_by_outlet`에 나타난다.
- `POST /api/purge-disallowed-articles` — 화이트리스트를 수정한 뒤, 이미 저장된 목록 밖 언론사의
  과거 기사를 정리하고 싶을 때 호출한다 (`sync_pipeline.purge_disallowed_articles`).

## 네이버 API 사용 규칙
- 인증: `X-Naver-Client-Id` / `X-Naver-Client-Secret` 헤더. 값은 `.env`의
  `NAVER_CLIENT_ID` / `NAVER_CLIENT_SECRET`에서 로드한다 (`backend/config.py`).
  **코드에 하드코딩 금지**, `.env`는 `.gitignore` 처리되어 있다.
- 요청 제한 대응: 키워드별 순차 호출 + 실패 시 최대 2회 재시도(지수적 딜레이).
  상수는 `backend/config.py`의 `NAVER_REQUEST_DELAY_SEC`, `NAVER_MAX_RETRIES`.
- 엔드포인트: `GET https://openapi.naver.com/v1/search/news.json` (`sort=date`, `display<=100`).

## 데이터 스키마
- `keywords`: `id, keyword(UNIQUE), created_at`
- `articles`: `id, link(UNIQUE), title, description, pub_date, synced_at`
- `article_keywords`: `article_id, keyword_id` (다대다, `link` 기준 upsert 시 합집합으로 병합)
- `meta`: `key, value` (예: `last_sync_at`)
- 상세 CRUD는 `backend/services/storage.py` 참고.

## 훅/게이트 동작 방식 요약
`.claude/settings.json`의 `PostToolUse` 훅이 Edit/Write/MultiEdit마다
`.claude/hooks/gate_dispatch.py`를 실행한다. 이 스크립트는 수정된 파일 경로를 보고:
- `backend/**/*.py` → `pytest backend/tests -q` 실행, 실패 시 종료코드 1 + stderr에 실패 로그
- `output/_raw/*.json` → 네이버 API 원시 응답 형식(`items` 키 존재)인지 최소 확인
- 그 외 파일 → 아무 것도 하지 않고 통과

**`output/_pipeline_state.json`은 `backend/services/pipeline_state.py`의 `record_step()`을 통해서만
기록된다. 사람이나 에이전트가 직접 편집하지 않는다.**

## 멱등 규칙
- 기준 키: 기사의 `link`
- 재동기화 시 동일 `link`는 `articles` 테이블에서 upsert(제목/설명/발행일 갱신)하고,
  `article_keywords`는 기존 태그 + 신규 매칭 태그를 합집합으로 병합한다 (`storage.upsert_article`).
- 신규 키워드 추가 후에도 과거에 이미 저장된 기사에 대한 소급 재매칭은 하지 않는다
  (설계서 2.3 분기 조건. 필요 시 향후 "전체 재매칭" 기능으로 확장).

## 실행 방법
```bash
pip install -r requirements.txt
cp .env.example .env   # NAVER_CLIENT_ID / NAVER_CLIENT_SECRET 입력
uvicorn backend.main:app --reload
# 브라우저에서 http://localhost:8000 접속
```

## 테스트/검증 실행 방법
```bash
python -m pytest backend/tests -q
```
스모크 테스트: 대시보드에서 키워드 추가 → "지금 업데이트" 클릭 → 키워드 탭에 기사가
표시되는지, 재클릭 시 중복 기사가 늘어나지 않는지 확인한다.

## 비밀번호 게이트 (공개 배포용)
로컬이 아닌 웹으로 배포하면 누구나 URL에 접속해 키워드를 조작하거나 "업데이트" 버튼으로
네이버 API 할당량을 소모시킬 수 있어, 페이지 진입 시 비밀번호를 한 번 입력하면 이후 자유롭게
쓸 수 있는 간단한 게이트를 추가했다.
- `backend/services/auth.py` — `APP_PASSWORD`(단일 비밀번호)와 `SESSION_SECRET`(쿠키 서명키)으로
  HMAC 서명된 세션 토큰을 발급/검증한다. 별도 사용자 계정·DB 테이블 없이 쿠키 하나로 처리하는
  경량 방식이다.
- `APP_PASSWORD`를 설정하지 않으면 인증이 완전히 꺼진다 (로컬 개발 시 비밀번호 없이 바로 사용).
  **배포 시에는 반드시 설정해야 한다.**
- `SESSION_SECRET`을 설정하지 않으면 `output/.session_secret`에 자동 생성되어 저장되는데,
  컨테이너 재배포 시 파일시스템이 초기화되는 플랫폼(영구 디스크 미사용 시)에서는 재배포할 때마다
  값이 바뀌어 기존 로그인이 모두 풀린다. 배포 시 `SESSION_SECRET`을 직접 고정하는 것을 권장한다.
- 보호 대상: `/api/keywords`, `/api/sync`, `/api/articles` (라우터 단위로 `Depends(require_auth)`
  적용). `/api/login`, `/api/me`, `/api/logout`과 정적 프런트엔드 파일은 인증 없이 접근 가능하다
  (로그인 페이지 자체는 보여줘야 하므로).
- 프런트엔드: `frontend/index.html`의 `#login-overlay`가 페이지 로드 시 `/api/me`를 호출해
  인증 여부를 확인하고, 미인증 시 비밀번호 모달을 띄운다 (`frontend/app.js`의 `checkAuthAndInit`).

## 배포 (Render 기준)
Docker 기반 배포를 전제로 `Dockerfile` / `.dockerignore` / `render.yaml`을 준비해 두었다.
SQLite를 그대로 쓰므로, 컨테이너가 재시작되어도 데이터가 사라지지 않도록 **영구 디스크가 필수**다.

1. 이 저장소를 GitHub에 올린다 (`git init` 및 최초 커밋은 이미 되어 있음 — `git remote add origin ...` 후 `git push`만 하면 됨).
2. [Render 대시보드](https://dashboard.render.com)에서 "New +" → "Blueprint"로 위 GitHub 저장소를 연결하면
   `render.yaml`을 읽어 웹 서비스 + 1GB 영구 디스크(`/data`)를 자동으로 구성한다.
   (`render.yaml`의 `plan: starter`는 Render의 유료 최저 플랜이다 — 무료 플랜은 영구 디스크를 지원하지 않는다.)
3. Render 대시보드의 Environment 탭에서 아래 값을 채운다 (`render.yaml`에는 `sync: false`로 되어 있어
   저장소에는 값이 들어가지 않고, 배포 시 대시보드에서 직접 입력해야 한다):
   - `NAVER_CLIENT_ID`, `NAVER_CLIENT_SECRET` — 네이버 개발자센터에서 발급받은 값
   - `APP_PASSWORD` — 대시보드 접속 비밀번호
   - `SESSION_SECRET` — `python -c "import secrets; print(secrets.token_hex(32))"`로 생성한 임의의 긴 문자열
4. 배포가 끝나면 Render가 제공하는 `https://<서비스명>.onrender.com` 주소로 접속해 비밀번호 게이트가
   뜨는지, 로그인 후 정상 동작하는지 확인한다.
5. 자동 스케줄 동기화가 필요하면, Render의 "Cron Job" 리소스를 추가로 만들어
   `curl -X POST https://<서비스명>.onrender.com/api/sync -H "Cookie: session_token=<유효한 토큰>"`
   형태로 호출하거나, 더 간단히는 배포된 서비스에 매일 접속해 "지금 업데이트" 버튼을 누르는 방식으로 운용한다
   (설계서 범위상 자동 스케줄링은 필수 기능이 아니다).

다른 플랫폼(Fly.io, Railway 등)도 Dockerfile 기반이라 동일하게 배포 가능하다 — 영구 디스크/볼륨을
붙이고 위와 같은 환경변수를 설정하면 된다.
