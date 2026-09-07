from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_classify_waste_returns_deterministic_fallback() -> None:
    response = client.post(
        "/api/v1/ai/classify-waste",
        files={"image": ("kitchen-scrap.jpg", b"mock-image-bytes", "image/jpeg")},
    )

    assert response.status_code == 200
    assert response.json() == {
        "detected_materials": [
            {"material_code": "pet_plastic", "confidence": "0.94", "estimated_kg": "4.50"},
            {"material_code": "cardboard", "confidence": "0.88", "estimated_kg": "3.00"},
        ],
        "contamination_detected": False,
        "confidence_score": "0.91",
        "fallback_used": True,
    }


def test_classify_waste_requires_a_file() -> None:
    response = client.post("/api/v1/ai/classify-waste")

    assert response.status_code == 422