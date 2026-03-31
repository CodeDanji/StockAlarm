from __future__ import annotations

import base64
import json
import os
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from app.services.job_dispatcher import run_named_worker_job

router = APIRouter(tags=["internal"])


def _decode_pubsub_payload(envelope: dict[str, Any]) -> dict[str, Any]:
    message = envelope.get("message")
    if not isinstance(message, dict):
        raise ValueError("invalid pubsub envelope")

    encoded_data = message.get("data")
    if not encoded_data:
        return {}

    try:
        decoded = base64.b64decode(str(encoded_data)).decode("utf-8")
        payload = json.loads(decoded)
    except Exception as exc:  # noqa: BLE001
        raise ValueError("invalid pubsub message data") from exc

    if not isinstance(payload, dict):
        raise ValueError("pubsub payload must be a json object")
    return payload


def _verify_internal_token(token: str) -> None:
    expected = os.getenv("INTERNAL_DISPATCH_TOKEN", "").strip()
    if not expected:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="internal dispatch token is not configured",
        )
    if token.strip() != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid dispatch token",
        )


@router.post("/internal/dispatch/{job_key}", status_code=status.HTTP_202_ACCEPTED)
def dispatch_worker_job(job_key: str, envelope: dict[str, Any], token: str = Query(default="")) -> dict[str, Any]:
    _verify_internal_token(token)

    try:
        payload = _decode_pubsub_payload(envelope)
        result = run_named_worker_job(job_key=job_key, payload=payload)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return {"status": "accepted", **result, "payload": payload}
