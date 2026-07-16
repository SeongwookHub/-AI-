from unittest.mock import patch

from fastapi.testclient import TestClient

from backend.main import app


def test_unhandled_exception_returns_clean_500_not_raw_traceback():
    client = TestClient(app, raise_server_exceptions=False)

    with patch("backend.routes.keywords.storage.list_keywords", side_effect=RuntimeError("boom")):
        response = client.get("/api/keywords")

    assert response.status_code == 500
    assert response.json() == {"detail": "서버에서 예상하지 못한 오류가 발생했습니다. 잠시 후 다시 시도해주세요."}
    assert "RuntimeError" not in response.text  # 스택트레이스가 그대로 노출되지 않아야 함


def test_deliberate_http_exception_is_not_swallowed_by_global_handler():
    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/api/articles", params={"keyword_id": 999999})

    assert response.status_code == 404
    assert response.json() == {"detail": "존재하지 않는 키워드입니다."}
