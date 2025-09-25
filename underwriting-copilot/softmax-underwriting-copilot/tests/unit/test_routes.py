from __future__ import annotations

from fastapi.testclient import TestClient


def test_health_endpoints(client: TestClient) -> None:
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"

    ready = client.get("/readyz")
    assert ready.status_code == 200


def test_root_endpoint(client: TestClient) -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "up"
