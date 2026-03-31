from __future__ import annotations

import base64
import json

from fastapi.testclient import TestClient

from app.main import app


def _pubsub_envelope(payload: dict) -> dict:
    encoded = base64.b64encode(json.dumps(payload).encode("utf-8")).decode("utf-8")
    return {
        "message": {
            "data": encoded,
            "messageId": "1",
        },
        "subscription": "projects/test/subscriptions/s1",
    }


def test_internal_dispatch_accepts_and_runs_job(monkeypatch) -> None:
    monkeypatch.setenv("INTERNAL_DISPATCH_TOKEN", "secret")
    monkeypatch.setattr(
        "app.routers.internal_dispatch.run_named_worker_job",
        lambda *, job_key, payload: {
            "job_name": f"ecoalarm-{job_key}",
            "operation": "operations/abc123",
            "payload": payload,
        },
    )

    client = TestClient(app)
    response = client.post(
        "/internal/dispatch/ingestor?token=secret",
        json=_pubsub_envelope({"scope": "market_hours", "timeframe": "15m"}),
    )

    assert response.status_code == 202
    body = response.json()
    assert body["status"] == "accepted"
    assert body["job_name"] == "ecoalarm-ingestor"
    assert body["payload"] == {"scope": "market_hours", "timeframe": "15m"}


def test_internal_dispatch_rejects_invalid_token(monkeypatch) -> None:
    monkeypatch.setenv("INTERNAL_DISPATCH_TOKEN", "secret")
    client = TestClient(app)

    response = client.post(
        "/internal/dispatch/ingestor?token=wrong",
        json=_pubsub_envelope({"scope": "market_hours"}),
    )

    assert response.status_code == 401
