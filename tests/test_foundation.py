from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_root_reports_ready_service() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {
        "name": "Kabadiwala Connect OS",
        "status": "ready",
        "version": "0.1.0",
    }


def test_health_check() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_material_catalog_uses_decimal_safe_json_values() -> None:
    response = client.get("/api/v1/materials?material_code=pet_plastic")

    assert response.status_code == 200
    assert response.json() == [
        {
            "material_code": "pet_plastic",
            "display_name": "PET Plastic",
            "aggregator_buy_rate": "42.00",
            "collector_margin": "4.00",
            "density_kg_per_m3": "35.00",
            "co2e_factor": "1.450",
        }
    ]


def test_unknown_material_returns_empty_list() -> None:
    response = client.get("/api/v1/materials?material_code=unknown")

    assert response.status_code == 200
    assert response.json() == []
