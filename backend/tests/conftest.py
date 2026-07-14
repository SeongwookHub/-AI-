import pytest

from backend.services import storage


@pytest.fixture
def temp_storage(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "DB_PATH", tmp_path / "test_articles.db")
    storage.init_db()
    return storage
