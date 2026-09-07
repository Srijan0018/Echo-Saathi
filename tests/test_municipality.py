from fastapi.testclient import TestClient

from app.main import BATCHES, FRAUD_AUDIT_LOGS, PICKUPS, USERS, app


client = TestClient(app)


def setup_function() -> None:
    USERS.clear()
    PICKUPS.clear()
    BATCHES.clear()
    FRAUD_AUDIT_LOGS.clear()


def test_municipality_summary_is_empty_at_start() -> None:
    response = client.get("/api/v1/municipality/summary")

    assert response.status_code == 200
    assert response.json() == {
        "pickups_completed": 0,
        "recovered_weight_kg": "0.00",
        "processed_batches": 0,
        "active_collectors": 0,
        "fraud_audit_flags": 0,
    }


def test_municipality_summary_counts_collectors_and_completed_pickups() -> None:
    client.post(
        "/api/v1/auth/register",
        json={"phone": "+919876543210", "full_name": "Ravi Kumar", "role": "collector"},
    )
    client.post(
        "/api/v1/auth/register",
        json={"phone": "+919876543211", "full_name": "Asha Devi", "role": "citizen"},
    )

    response = client.get("/api/v1/municipality/summary")

    assert response.status_code == 200
    assert response.json()["active_collectors"] == 1
    assert response.json()["pickups_completed"] == 0