from __future__ import annotations

import json

import pytest

import app.services.job_dispatcher as job_dispatcher


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self.payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict:
        return self.payload


class _FakeHTTPClient:
    def __init__(self) -> None:
        self.calls: list[tuple[str, dict, dict]] = []

    def post(self, url: str, headers: dict, json: dict) -> _FakeResponse:
        self.calls.append((url, headers, json))
        return _FakeResponse({"name": "operations/run-123"})


def test_cloud_run_job_dispatcher_posts_run_request() -> None:
    fake_http = _FakeHTTPClient()
    dispatcher = job_dispatcher.CloudRunJobDispatcher(
        project_id="proj-1",
        region="asia-northeast3",
        http_client=fake_http,
        token_provider=lambda: "token-xyz",
    )

    result = dispatcher.run_job(job_name="ecoalarm-ingestor", payload={"scope": "market_hours"})

    assert result["job_name"] == "ecoalarm-ingestor"
    assert result["operation"] == "operations/run-123"
    assert fake_http.calls
    url, headers, body = fake_http.calls[0]
    assert url.endswith("/projects/proj-1/locations/asia-northeast3/jobs/ecoalarm-ingestor:run")
    assert headers["Authorization"] == "Bearer token-xyz"
    encoded_payload = body["overrides"]["containerOverrides"][0]["env"][0]["value"]
    assert json.loads(encoded_payload) == {"scope": "market_hours"}


def test_run_named_worker_job_rejects_unknown_key() -> None:
    with pytest.raises(ValueError, match="unknown worker job key"):
        job_dispatcher.run_named_worker_job(job_key="unknown", payload={})
