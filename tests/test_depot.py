from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_depot_console_is_served() -> None:
    response = client.get("/depot/depot.html")

    assert response.status_code == 200
    assert "Create freight batch" in response.text
    assert client.get("/depot/depot.js").status_code == 200