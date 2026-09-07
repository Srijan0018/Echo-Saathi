from fastapi.testclient import TestClient

from app.main import USERS, app


client = TestClient(app)


def setup_function() -> None:
    USERS.clear()


def test_register_and_verify_mock_kyc() -> None:
    registration = client.post(
        "/api/v1/auth/register",
        json={
            "phone": "+919876543210",
            "full_name": "Ravi Kumar",
            "role": "collector",
            "upi_id": "ravi@upi",
        },
    )

    assert registration.status_code == 201
    user = registration.json()
    assert user["dpi_kyc_verified"] is False

    kyc = client.post(
        "/api/v1/dpi/verify-kyc",
        json={"user_id": user["id"], "reference_token": "DPI-MOCK-TOKEN"},
    )

    assert kyc.status_code == 200
    assert kyc.json()["status"] == "VERIFIED"
    assert "DPI-MOCK-TOKEN" not in str(USERS)
    assert USERS[next(iter(USERS))].dpi_kyc_verified is True


def test_duplicate_phone_is_rejected() -> None:
    payload = {"phone": "919876543210", "full_name": "Asha Devi", "role": "citizen"}
    assert client.post("/api/v1/auth/register", json=payload).status_code == 201
    assert client.post("/api/v1/auth/register", json=payload).status_code == 409


def test_unknown_kyc_user_is_rejected() -> None:
    response = client.post(
        "/api/v1/dpi/verify-kyc",
        json={
            "user_id": "00000000-0000-0000-0000-000000000000",
            "reference_token": "DPI-MOCK-TOKEN",
        },
    )

    assert response.status_code == 404