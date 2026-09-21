from fastapi.testclient import TestClient

from wafi.api.app import app


def test_health_is_always_ok():
    with TestClient(app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200


def test_ready_after_startup():
    with TestClient(app) as client:
        resp = client.get("/ready")
        assert resp.status_code == 200


def test_predict_valid_request_returns_envelope():
    with TestClient(app) as client:
        resp = client.post("/v1/predict", json={"text": "my laptop screen is flickering"})
        assert resp.status_code == 200
        body = resp.json()
        assert "trace_id" in body
        assert body["data"]["team"] in {"network", "hardware", "software", "accounts", "general"}


def test_predict_rejects_unknown_fields():
    with TestClient(app) as client:
        resp = client.post(
            "/v1/predict",
            json={"text": "hello", "some_unexpected_field": "x"},
        )
        assert resp.status_code == 422


def test_predict_rejects_empty_text():
    with TestClient(app) as client:
        resp = client.post("/v1/predict", json={"text": ""})
        assert resp.status_code == 422
