from uuid import uuid4

from app.database import persist_batch, persist_recycle


def test_batch_persistence_is_disabled_without_database_url(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    assert persist_batch(uuid4(), "a" * 64, uuid4(), "pet_plastic", "5.00", [uuid4()]) is False
    assert persist_recycle(
        uuid4(), "10.00", "0.00", "4.50", "6.53", "EPR-DEMO", "digilocker://demo"
    ) is False