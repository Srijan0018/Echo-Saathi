from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_dashboard_is_served_by_api() -> None:
    response = client.get("/dashboard/")

    assert response.status_code == 200
    assert "Recovery command centre" in response.text
    assert "/dashboard/styles.css" in response.text