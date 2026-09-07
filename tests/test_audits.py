from decimal import Decimal
from uuid import uuid4

from fastapi.testclient import TestClient

from app.main import FRAUD_AUDIT_LOGS, app


client = TestClient(app)


def setup_function() -> None:
    FRAUD_AUDIT_LOGS.clear()


def test_municipality_audits_returns_typed_review_records() -> None:
    collector_id = uuid4()
    pickup_id = uuid4()
    FRAUD_AUDIT_LOGS.append(
        {
            "collector_id": collector_id,
            "pickup_id": pickup_id,
            "calculated_z_score": Decimal("3.20"),
            "flagged_reason": "z_score_exceeds_2.5",
        }
    )

    response = client.get("/api/v1/municipality/audits")

    assert response.status_code == 200
    assert response.json() == [
        {
            "collector_id": str(collector_id),
            "pickup_id": str(pickup_id),
            "calculated_z_score": "3.20",
            "flagged_reason": "z_score_exceeds_2.5",
        }
    ]