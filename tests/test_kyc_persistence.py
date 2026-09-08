from uuid import uuid4

from app.database import persist_kyc


def test_kyc_persistence_is_disabled_without_database_url(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    assert persist_kyc(uuid4(), "a" * 64) is False