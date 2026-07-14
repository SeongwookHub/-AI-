import os
import secrets
from pathlib import Path

from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent

load_dotenv(PROJECT_ROOT / ".env")

# 배포 환경(예: Render 영구 디스크)에서는 DATA_DIR을 마운트된 경로로 지정한다.
# 로컬 개발에서는 지정하지 않으면 프로젝트 내 output/ 폴더를 그대로 쓴다.
OUTPUT_DIR = Path(os.getenv("DATA_DIR", PROJECT_ROOT / "output"))
RAW_DIR = OUTPUT_DIR / "_raw"
DB_PATH = OUTPUT_DIR / "articles.db"
PIPELINE_STATE_PATH = OUTPUT_DIR / "_pipeline_state.json"
SESSION_SECRET_PATH = OUTPUT_DIR / ".session_secret"

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET")

# 네이버 뉴스 검색 API 요청 제한 대응: 키워드 호출 사이 최소 대기시간(초)
NAVER_REQUEST_DELAY_SEC = 0.3
NAVER_MAX_RETRIES = 2

# 대시보드 전체를 잠그는 단일 비밀번호. 미설정 시 인증 없이 접근 가능(로컬 개발용).
APP_PASSWORD = os.getenv("APP_PASSWORD")


def _load_or_create_session_secret() -> str:
    env_secret = os.getenv("SESSION_SECRET")
    if env_secret:
        return env_secret
    if SESSION_SECRET_PATH.exists():
        return SESSION_SECRET_PATH.read_text(encoding="utf-8").strip()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    secret = secrets.token_hex(32)
    SESSION_SECRET_PATH.write_text(secret, encoding="utf-8")
    return secret


# 세션 쿠키 서명용 비밀키. 배포 시 SESSION_SECRET 환경변수로 고정하는 것을 권장한다
# (설정하지 않으면 재배포/재시작 때마다 값이 바뀌어 기존 로그인 세션이 모두 풀린다).
SESSION_SECRET = _load_or_create_session_secret()


def require_naver_credentials():
    if not NAVER_CLIENT_ID or not NAVER_CLIENT_SECRET:
        raise RuntimeError(
            "네이버 API 키가 설정되지 않았습니다. "
            ".env 파일에 NAVER_CLIENT_ID / NAVER_CLIENT_SECRET을 설정하세요. "
            "(.env.example 참고)"
        )
