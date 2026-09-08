from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_collector_console_is_served() -> None:
    response = client.get("/collector/collector.html")

    assert response.status_code == 200
    assert "Assign pickup to me" in response.text
    assert "Load my open pickups" in response.text
    assert client.get("/collector/collector.js").status_code == 200