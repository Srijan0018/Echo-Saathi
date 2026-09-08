from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_citizen_pickup_page_is_served() -> None:
    response = client.get("/citizen/citizen.html")

    assert response.status_code == 200
    assert "Book collector pickup" in response.text
    assert "RWA bulk drive" in response.text
    assert client.get("/citizen/citizen.js").status_code == 200