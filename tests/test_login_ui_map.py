from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_login_page_and_dashboard_map_are_served() -> None:
    login = client.get("/login/login.html")
    dashboard = client.get("/dashboard/")

    assert login.status_code == 200
    assert "Continue" in login.text
    assert "/login/login.js" in login.text
    assert dashboard.status_code == 200
    assert "Pickup activity map" in dashboard.text