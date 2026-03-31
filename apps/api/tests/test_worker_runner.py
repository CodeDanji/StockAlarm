from __future__ import annotations

import json

import pytest

from app.workers import runner


def test_load_payload_json_returns_empty_without_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DISPATCH_PAYLOAD_JSON", raising=False)
    assert runner.load_payload_json() == {}


def test_load_payload_json_rejects_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("DISPATCH_PAYLOAD_JSON", "not-json")
    with pytest.raises(ValueError, match="invalid DISPATCH_PAYLOAD_JSON"):
        runner.load_payload_json()


def test_run_worker_ingestor_uses_scope_from_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.workers.runner.run_ingestion_cycle",
        lambda scope: {"worker": "ingestor", "scope": scope},
    )
    result = runner.run_worker(worker_key="ingestor", payload={"scope": "off_hours"})
    assert result == {"worker": "ingestor", "scope": "off_hours"}


def test_run_worker_digest_ignores_payload(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "app.workers.runner.run_morning_digest",
        lambda: {"worker": "digest", "status": "ok"},
    )
    result = runner.run_worker(worker_key="digest", payload={"scope": "ignored"})
    assert result == {"worker": "digest", "status": "ok"}


def test_main_returns_error_for_unknown_worker(capsys: pytest.CaptureFixture[str]) -> None:
    code = runner.main(["--worker", "unknown"])
    captured = capsys.readouterr()
    assert code == 2
    assert "unknown worker key" in captured.err


def test_main_prints_json_on_success(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(
        "app.workers.runner.run_worker",
        lambda worker_key, payload: {"worker": worker_key, "payload": payload},
    )
    monkeypatch.setenv("DISPATCH_PAYLOAD_JSON", json.dumps({"scope": "market_hours"}))

    code = runner.main(["--worker", "evaluator"])
    captured = capsys.readouterr()

    assert code == 0
    assert json.loads(captured.out) == {
        "worker": "evaluator",
        "payload": {"scope": "market_hours"},
    }
