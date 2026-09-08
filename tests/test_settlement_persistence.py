from uuid import uuid4

from app.database import persist_settlement


def test_settlement_persistence_is_disabled_without_database_url(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    assert persist_settlement(
        uuid4(),
        uuid4(),
        [("pet_plastic", "5.00", "0.00", "190.00", "7.25")],
    ) is False