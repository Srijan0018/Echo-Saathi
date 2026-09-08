from uuid import uuid4

from app.database import persist_pickup


def test_pickup_persistence_is_disabled_without_database_url(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    assert persist_pickup(
        uuid4(),
        uuid4(),
        "12.971600",
        "77.594600",
        "4826",
        [("pet_plastic", "4.50")],
    ) is False