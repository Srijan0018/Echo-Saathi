from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_regulatory_query_returns_exact_citation() -> None:
    response = client.post("/api/v1/rag/query", json={"query": "plastic packaging EPR"})

    assert response.status_code == 200
    assert response.json()["citations"][0]["citation"] == "Plastic Waste Management Rules, 2016, Rule 9"
    assert "extended producer responsibility" in response.json()["answer"]


def test_regulatory_query_degrades_when_no_rule_matches() -> None:
    response = client.post("/api/v1/rag/query", json={"query": "unrelated topic"})

    assert response.status_code == 200
    assert response.json()["citations"] == []