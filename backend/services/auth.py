import base64
import hashlib
import hmac
import time

from fastapi import HTTPException, Request

from backend.config import APP_PASSWORD, SESSION_SECRET

SESSION_COOKIE_NAME = "session_token"
SESSION_MAX_AGE_SECONDS = 30 * 24 * 60 * 60  # 30일


def _sign(payload: str) -> str:
    return hmac.new(SESSION_SECRET.encode(), payload.encode(), hashlib.sha256).hexdigest()


def create_session_token() -> str:
    expires_at = int(time.time()) + SESSION_MAX_AGE_SECONDS
    payload = str(expires_at)
    raw = f"{payload}.{_sign(payload)}"
    return base64.urlsafe_b64encode(raw.encode()).decode()


def verify_session_token(token: str | None) -> bool:
    if not token:
        return False
    try:
        raw = base64.urlsafe_b64decode(token.encode()).decode()
        payload, signature = raw.rsplit(".", 1)
    except (ValueError, UnicodeDecodeError, base64.binascii.Error):
        return False
    if not hmac.compare_digest(_sign(payload), signature):
        return False
    return int(payload) >= int(time.time())


def is_auth_enabled() -> bool:
    return bool(APP_PASSWORD)


def require_auth(request: Request) -> None:
    """비밀번호가 설정되지 않았으면(로컬 개발) 인증을 건너뛴다."""
    if not is_auth_enabled():
        return
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if not verify_session_token(token):
        raise HTTPException(status_code=401, detail="로그인이 필요합니다.")
