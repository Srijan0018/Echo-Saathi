from fastapi.testclient import TestClient

from app.main import BATCHES, PICKUPS, SETTLED_WEIGHTS, USERS, app


client = TestClient(app)


def setup_function() -> None:
    USERS.clear()
    PICKUPS.clear()
    SETTLED_WEIGHTS.clear()
    BATCHES.clear()


def test_batch_aggregation_and_recycling_issue_outputs() -> None:
    citizen = client.post(
        "/api/v1/auth/register",
        json={"phone": "+919876543210", "full_name": "Asha Devi", "role": "citizen"},
    ).json()
    collector = client.post(
        "/api/v1/auth/register",
        json={"phone": "+919876543211", "full_name": "Ravi Kumar", "role": "collector"},
    ).json()
    aggregator = client.post(
        "/api/v1/auth/register",
        json={"phone": "+919876543212", "full_name": "Depot One", "role": "aggregator"},
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
    client.post(
        "/api/v1/pickups/verify-and-settle",
        json={
            "pickup_id": pickup["id"],
            "collector_id": collector["id"],
            "otp_code": "4826",
            "items": [{"material_code": "pet_plastic", "actual_weight_kg": "5.00", "quality_deduction_pct": "0"}],
        },
    )

    batch = client.post(
        "/api/v1/batches/aggregate",
        json={"aggregator_id": aggregator["id"], "material_code": "pet_plastic", "pickup_ids": [pickup["id"]]},
    )
    assert batch.status_code == 201
    assert batch.json()["gross_weight_kg"] == "5.00"

    recycled = client.put(
        f"/api/v1/batches/{batch.json()['batch_id']}/recycle",
        json={"moisture_deduction_pct": "10.00", "foreign_matter_deduction_pct": "0"},
    )
    assert recycled.status_code == 200
    assert recycled.json()["net_weight_kg"] == "4.50"
    assert recycled.json()["cpcb_epr_token"].startswith("EPR-")
    assert recycled.json()["co2e_avoided_kg"] == "6.53"
    assert recycled.json()["digilocker_doc_uri"].startswith("digilocker://issuer/kabadiwala/batches/")