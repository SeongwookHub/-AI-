# 📈 KStock Hub

관심 있는 코스피/코스닥 종목을 등록해두면, 관련 뉴스와 실시간 시세를 한 곳에서 볼 수 있는
개인용 주식 뉴스 대시보드입니다.

## 주요 기능

- **종목 검색·등록**: 종목명 또는 6자리 종목코드로 검색(대소문자 구분 없음), 검색 결과에서
  바로 추가. 코스피/코스닥에 실제 상장된 종목(ETF/ETN 제외)만 등록 가능하며, 최근 검색어는
  개인 브라우저에만 저장되어 원할 때 지울 수 있습니다.
- **뉴스 자동 수집**: 종목을 추가하면 즉시 관련 뉴스를 동기화하고, 이후에도 "지금 업데이트"
  버튼으로 언제든 최신화할 수 있습니다. 네이버 뉴스 검색 API를 사용하며, 정치/경제/사회/
  생활문화/IT과학/세계 6개 섹터의 주요 언론사 화이트리스트로 필터링합니다.
- **시간대별 뉴스 분류**: 1시간 이내 / 3시간 이내 / 오늘 / 어제 이전 구간으로 나눠서 보여주고,
  각 구간은 접었다 펼 수 있습니다. 기사 안에서 종목명이 언급된 부분은 노란색으로 하이라이트됩니다.
- **실시간 시세 패널**: 네이버 증권 기준 KRX(코스피/코스닥 정규장)와 NXT(넥스트레이드) 시세를
  함께 보여주고, 장중/시간외/장마감 상태를 색으로 구분합니다. 일봉 차트를 누르면 네이버 증권
  종목 페이지로 이동합니다.
- **증권사 리포트**: 최근 리포트 최대 4건을 제목/증권사/날짜와 함께 보여주고, 온라인으로 읽거나
  PDF로 바로 다운로드할 수 있습니다.
- **비밀번호 게이트**: 공개 배포 시 페이지 진입 시 비밀번호 입력 화면이 뜨고, 통과하면 이후
  자유롭게 사용할 수 있습니다.

## 기술 스택

- 백엔드: Python, FastAPI, SQLite
- 프런트엔드: 순수 HTML/CSS/JavaScript (별도 빌드 과정 없음)
- 배포: Docker, [Render](https://render.com)

## 프로젝트 구조

```
backend/
  main.py              # FastAPI 앱 진입점
  config.py             # 환경변수 로딩, 경로 상수
  routes/               # keywords / stocks / sync / articles / auth 엔드포인트
  services/              # 네이버 API 연동, 종목 검색, 시세, 리포트, 인증 등 핵심 로직
  models/schemas.py       # API 요청/응답 스키마
  tests/                 # pytest 단위 테스트
frontend/
  index.html / app.js / style.css   # 정적 대시보드 (빌드 도구 없이 바로 서빙)
output/                  # SQLite DB, 종목 캐시 등 실행 중 생성되는 데이터 (git에는 포함 안 됨)
.claude/                 # 이 프로젝트를 Claude Code로 개발/유지보수할 때 쓰는 스킬·훅 설정
Dockerfile, render.yaml   # 배포 설정
```

## 로컬 실행

```bash
pip install -r requirements.txt
cp .env.example .env   # 아래 환경변수를 채운다
uvicorn backend.main:app --reload
# http://localhost:8000 접속
```

### 환경변수 (`.env`)

| 변수 | 설명 |
|---|---|
| `NAVER_CLIENT_ID` / `NAVER_CLIENT_SECRET` | [네이버 개발자센터](https://developers.naver.com/apps/#/register)에서 "검색" API로 발급받은 값 |
| `APP_PASSWORD` | 대시보드 접속 비밀번호. 비워두면 인증 없이 접근 가능(로컬 개발용) |
| `SESSION_SECRET` | 로그인 세션 쿠키 서명용 비밀키. 비워두면 자동 생성되지만, 배포 환경에서는 고정 값을 권장 |
| `DATA_DIR` | SQLite/캐시 저장 경로. 비워두면 프로젝트 내 `output/` 사용 |

## 테스트

```bash
python -m pytest backend/tests -q
```

## 배포 (Render)

1. 이 저장소를 GitHub에 push
2. Render 대시보드에서 **New +** → **Blueprint**로 저장소 연결 (`render.yaml`을 자동 인식)
3. Environment 탭에서 위 표의 환경변수 입력 (저장소에는 값이 들어가지 않으므로 직접 입력 필요)
4. 배포 완료 후 발급된 주소로 접속

무료 플랜은 일정 시간 요청이 없으면 인스턴스가 잠들고, 재시작 시 데이터가 초기화될 수 있습니다.
데이터를 계속 유지하려면 영구 디스크가 있는 유료 플랜으로 전환하세요.

## 데이터 출처와 유의사항

- 뉴스: [네이버 뉴스 검색 API](https://developers.naver.com/docs/serviceapi/search/news/news.md) (공식 API)
- 종목 목록, 실시간 시세, 차트, 증권사 리포트: 네이버 증권(finance.naver.com)이 자체 페이지에서
  사용하는 내부 엔드포인트를 이용합니다. 공식 문서화된 API가 아니므로, 네이버 측 변경에 따라
  동작이 달라질 수 있습니다.
