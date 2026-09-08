from fastapi.testclient import TestClient

from app.main import PICKUPS, USERS, app


client = TestClient(app)


def setup_function() -> None:
    USERS.clear()
    PICKUPS.clear()


def test_collector_can_be_assigned_to_requested_pickup() -> None:
    citizen = client.post(
        "/api/v1/auth/register",
        json={"phone": "+919876543210", "full_name": "Asha Devi", "role": "citizen"},
    ).json()
    collector = client.post(
        "/api/v1/auth/register",
        json={"phone": "+919876543211", "full_name": "Ravi Kumar", "role": "collector"},
    ).json()
    pickup = client.post(
        "/api/v1/pickups/request",
        json={
            "citizen_id": citizen["id"],
            "latitude": 12.9716,
            "longitude": 77.5946,
            "items": [{"material_code": "pet_plastic", "ai_estimated_kg": "4.50"}],
        },
    ).json()

    response = client.post(
        "/api/v1/pickups/assign",
        json={"pickup_id": pickup["id"], "collector_id": collector["id"]},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "assigned"
    assert response.json()["collector_id"] == collector["id"]


def test_wrong_collector_cannot_settle_assigned_pickup() -> None:
    citizen = client.post(
        "/api/v1/auth/register",
        json={"phone": "+919876543210", "full_name": "Asha Devi", "role": "citizen"},
    ).json()
    assigned_collector = client.post(
        "/api/v1/auth/register",
        json={"phone": "+919876543211", "full_name": "Ravi Kumar", "role": "collector"},
    ).json()
    other_collector = client.post(
        "/api/v1/auth/register",
        json={"phone": "+919876543212", "full_name": "Mina Shah", "role": "collector"},
    ).json()
    pickup = client.post(
        "/api/v1/pickups/request",
        json={
            "citizen_id": citizen["id"],
            "latitude": 12.9716,
            "longitude": 77.5946,
            "items": [{"material_code": "glass", "ai_estimated_kg": "2.00"}],
        },
    ).json()
    client.post(
        "/api/v1/pickups/assign",
        json={"pickup_id": pickup["id"], "collector_id": assigned_collector["id"]},
    )

    response = client.post(
        "/api/v1/pickups/verify-and-settle",
        json={
            "pickup_id": pickup["id"],
            "collector_id": other_collector["id"],
            "otp_code": "4826",
            "items": [{"material_code": "glass", "actual_weight_kg": "2.00", "quality_deduction_pct": "0"}],
        },
    )

    assert response.status_code == 403