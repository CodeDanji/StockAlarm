from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any

from app.workers.digest import run_morning_digest
from app.workers.evaluator import run_evaluation_cycle
from app.workers.ingestor import run_ingestion_cycle


def load_payload_json() -> dict[str, Any]:
    raw_payload = os.getenv("DISPATCH_PAYLOAD_JSON", "").strip()
    if not raw_payload:
        return {}
    try:
        payload = json.loads(raw_payload)
    except json.JSONDecodeError as exc:
        raise ValueError("invalid DISPATCH_PAYLOAD_JSON") from exc
    if not isinstance(payload, dict):
        raise ValueError("DISPATCH_PAYLOAD_JSON must be an object")
    return payload


def run_worker(*, worker_key: str, payload: dict[str, Any]) -> dict[str, Any]:
    normalized = worker_key.strip().lower()
    if normalized == "ingestor":
        scope = str(payload.get("scope", "market_hours"))
        return run_ingestion_cycle(scope=scope)
    if normalized == "evaluator":
        scope = str(payload.get("scope", "market_hours"))
        return run_evaluation_cycle(scope=scope)
    if normalized == "digest":
        return run_morning_digest()
    raise ValueError("unknown worker key")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="EcoAlarm worker runner")
    parser.add_argument("--worker", required=True, help="ingestor | evaluator | digest")
    args = parser.parse_args(argv)

    try:
        payload = load_payload_json()
        result = run_worker(worker_key=args.worker, payload=payload)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001
        print(str(exc), file=sys.stderr)
        return 1

    print(json.dumps(result, separators=(",", ":"), sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
