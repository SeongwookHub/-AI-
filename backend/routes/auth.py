from fastapi import APIRouter, HTTPException, Request, Response

from backend.config import APP_PASSWORD
from backend.models.schemas import LoginRequest
from backend.services.auth import (
    SESSION_COOKIE_NAME,
    SESSION_MAX_AGE_SECONDS,
    create_session_token,
    is_auth_enabled,
    verify_session_token,
)

router = APIRouter(prefix="/api", tags=["auth"])


@router.get("/me")
def me(request: Request):
    if not is_auth_enabled():
        return {"authenticated": True, "auth_required": False}
    token = request.cookies.get(SESSION_COOKIE_NAME)
    return {"authenticated": verify_session_token(token), "auth_required": True}


@router.post("/login")
def login(payload: LoginRequest, response: Response):
    if not is_auth_enabled() or payload.password != APP_PASSWORD:
        raise HTTPException(status_code=401, detail="비밀번호가 올바르지 않습니다.")
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=create_session_token(),
        httponly=True,
        samesite="lax",
        max_age=SESSION_MAX_AGE_SECONDS,
    )
    return {"ok": True}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(SESSION_COOKIE_NAME)
    return {"ok": True}
