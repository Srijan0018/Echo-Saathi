from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_database_health_defaults_to_in_memory_mode(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)

    response = client.get("/health/database")

    assert response.status_code == 200
    assert response.json() == {"status": "not_configured", "mode": "in_memory"}