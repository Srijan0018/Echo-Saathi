from uuid import uuid4

from app.database import persist_user


def test_user_persistence_is_disabled_without_database_url(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    assert persist_user(uuid4(), "919876543210", "Demo User", "citizen", None) is False