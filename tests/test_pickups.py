from fastapi.testclient import TestClient

from app.main import PICKUPS, USERS, app


client = TestClient(app)


def setup_function() -> None:
    USERS.clear()
    PICKUPS.clear()


def test_request_pickup_assigns_demo_otp() -> None:
    citizen = client.post(
        "/api/v1/auth/register",
        json={"phone": "+919876543210", "full_name": "Asha Devi", "role": "citizen"},
    ).json()

    response = client.post(
        "/api/v1/pickups/request",
        json={
            "citizen_id": citizen["id"],
            "latitude": "12.971600",
            "longitude": "77.594600",
            "items": [{"material_code": "pet_plastic", "ai_estimated_kg": "4.50"}],
        },
    )

    assert response.status_code == 201
    assert response.json()["status"] == "requested"
    assert response.json()["otp_code"] == "4826"
    assert len(PICKUPS) == 1


def test_request_pickup_rejects_unknown_material() -> None:
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
            "items": [{"material_code": "organic", "ai_estimated_kg": 2}],
        },
    )

    assert response.status_code == 422


def test_collector_cannot_create_citizen_pickup() -> None:
    collector = client.post(
        "/api/v1/auth/register",
        json={"phone": "+919876543210", "full_name": "Ravi Kumar", "role": "collector"},
    ).json()

    response = client.post(
        "/api/v1/pickups/request",
        json={
            "citizen_id": collector["id"],
            "latitude": 12.9716,
            "longitude": 77.5946,
            "items": [{"material_code": "glass", "ai_estimated_kg": 2}],
        },
    )

    assert response.status_code == 403