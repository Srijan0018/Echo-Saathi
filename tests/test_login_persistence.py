from fastapi.testclient import TestClient

from app.main import USERS, app


client = TestClient(app)


def test_login_uses_in_memory_user_when_available() -> None:
    USERS.clear()
    registration = client.post(
        "/api/v1/auth/register",
        json={"phone": "+919876543210", "full_name": "Ravi Kumar", "role": "collector"},
    ).json()

    response = client.post(
        "/api/v1/auth/login",
        json={"phone": registration["phone"], "role": "collector"},
    )

    assert response.status_code == 200
    assert response.json()["user"]["id"] == registration["id"]