import pytest
from fastapi import HTTPException

from backend.services import auth


class FakeRequest:
    def __init__(self, cookies=None):
        self.cookies = cookies or {}


def test_verify_session_token_roundtrip():
    token = auth.create_session_token()
    assert auth.verify_session_token(token) is True


def test_verify_session_token_rejects_garbage():
    assert auth.verify_session_token("not-a-valid-token") is False
    assert auth.verify_session_token(None) is False


def test_verify_session_token_rejects_tampered_payload(monkeypatch):
    token = auth.create_session_token()
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    assert auth.verify_session_token(tampered) is False


def test_verify_session_token_rejects_expired(monkeypatch):
    monkeypatch.setattr(auth, "SESSION_MAX_AGE_SECONDS", -10)
    expired_token = auth.create_session_token()
    assert auth.verify_session_token(expired_token) is False


def test_require_auth_skips_when_password_not_set(monkeypatch):
    monkeypatch.setattr(auth, "APP_PASSWORD", None)
    auth.require_auth(FakeRequest())  # 예외 없이 통과해야 함


def test_require_auth_blocks_without_valid_cookie(monkeypatch):
    monkeypatch.setattr(auth, "APP_PASSWORD", "secret")
    with pytest.raises(HTTPException) as exc_info:
        auth.require_auth(FakeRequest())
    assert exc_info.value.status_code == 401


def test_require_auth_allows_with_valid_cookie(monkeypatch):
    monkeypatch.setattr(auth, "APP_PASSWORD", "secret")
    token = auth.create_session_token()
    auth.require_auth(FakeRequest(cookies={auth.SESSION_COOKIE_NAME: token}))
