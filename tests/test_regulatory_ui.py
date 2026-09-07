from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_regulatory_assistant_is_served() -> None:
    response = client.get("/regulatory/regulatory.html")

    assert response.status_code == 200
    assert "Find citation" in response.text
    assert client.get("/regulatory/regulatory.js").status_code == 200