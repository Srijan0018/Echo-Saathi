from fastapi.testclient import TestClient

from app.main import PICKUPS, USERS, app


client = TestClient(app)


def setup_function() -> None:
    USERS.clear()
    PICKUPS.clear()


def test_rwa_drive_requires_a_name() -> None:
    citizen = client.post(
        "/api/v1/auth/register",
        json={"phone": "+919876543210", "full_name": "Asha Devi", "role": "citizen"},
    ).json()

    response = client.post(
        "/api/v1/pickups/request",
        json={
            "citizen_id": citizen["id"],
            "latitude": 12.9716,
            "longitude": 77.5946,
            "is_rwa_drive": True,
            "items": [{"material_code": "cardboard", "ai_estimated_kg": "40.00"}],
        },
    )

    assert response.status_code == 422


def test_rwa_drive_returns_offline_sync_metadata() -> None:
    citizen = client.post(
        "/api/v1/auth/register",
        json={"phone": "+919876543210", "full_name": "Asha Devi", "role": "citizen"},
    ).json()

    response = client.post(
        "/api/v1/pickups/request",
        json={
            "citizen_id": citizen["id"],
            "latitude": 12.9716,
            "longitude": 77.5946,
            "is_rwa_drive": True,
            "rwa_name": "Green Meadows RWA",
            "items": [{"material_code": "cardboard", "ai_estimated_kg": "40.00"}],
        },
    )

    assert response.status_code == 201
    assert response.json()["is_rwa_drive"] is True
    assert response.json()["rwa_name"] == "Green Meadows RWA"
    assert len(response.json()["offline_sync_token"]) == 64