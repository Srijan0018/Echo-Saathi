from fastapi.testclient import TestClient

from app.main import PICKUP_LOCATIONS, PICKUPS, SESSIONS, USERS, app


client = TestClient(app)


def setup_function() -> None:
    USERS.clear()
    SESSIONS.clear()
    PICKUPS.clear()
    PICKUP_LOCATIONS.clear()


def test_role_login_returns_session_token() -> None:
    client.post(
        "/api/v1/auth/register",
        json={"phone": "+919876543210", "full_name": "Ravi Kumar", "role": "collector"},
    )

    response = client.post(
        "/api/v1/auth/login",
        json={"phone": "+919876543210", "role": "collector"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert len(response.json()["access_token"]) == 64


def test_map_returns_pickup_coordinates_and_status() -> None:
    citizen = client.post(
        "/api/v1/auth/register",
        json={"phone": "+919876543210", "full_name": "Asha Devi", "role": "citizen"},
    ).json()
    pickup = client.post(
        "/api/v1/pickups/request",
        json={
            "citizen_id": citizen["id"],
            "latitude": "12.980000",
            "longitude": "77.600000",
            "items": [{"material_code": "glass", "ai_estimated_kg": "2.00"}],
        },
    ).json()

    response = client.get("/api/v1/municipality/map")

    assert response.status_code == 200
    assert response.json()["points"][0]["pickup_id"] == pickup["id"]
    assert response.json()["points"][0]["status"] == "requested"