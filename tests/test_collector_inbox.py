from fastapi.testclient import TestClient

from app.main import PICKUPS, USERS, app


client = TestClient(app)


def setup_function() -> None:
    USERS.clear()
    PICKUPS.clear()


def test_collector_inbox_returns_open_and_assigned_pickups() -> None:
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

    response = client.get(f"/api/v1/collectors/{collector['id']}/pickups")
    assert response.status_code == 200
    assert response.json()["pickups"][0]["id"] == pickup["id"]

    client.post(
        "/api/v1/pickups/assign",
        json={"pickup_id": pickup["id"], "collector_id": collector["id"]},
    )
    assigned_response = client.get(f"/api/v1/collectors/{collector['id']}/pickups")
    assert assigned_response.json()["pickups"][0]["status"] == "assigned"