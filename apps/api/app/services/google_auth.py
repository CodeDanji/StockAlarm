from __future__ import annotations

import os
from typing import Any

GOOGLE_TOKEN_ISSUERS = {
    "accounts.google.com",
    "https://accounts.google.com",
}


def _get_allowed_client_ids() -> set[str]:
    raw = os.getenv("GOOGLE_CLIENT_IDS") or os.getenv("GOOGLE_CLIENT_ID") or ""
    ids = {item.strip() for item in raw.split(",") if item.strip()}
    if not ids:
        raise ValueError("google client id is not configured")
    return ids


def _verify_with_google(token: str) -> dict[str, Any]:
    try:
        from google.auth.transport.requests import Request
        from google.oauth2 import id_token as google_id_token
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("google-auth dependency is not installed") from exc

    return google_id_token.verify_oauth2_token(token, Request())


def _is_email_verified(value: object) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"true", "1", "yes"}
    return False


def verify_google_id_token(id_token: str) -> dict[str, str]:
    if not id_token or not id_token.strip():
        raise ValueError("invalid token")

    payload = _verify_with_google(id_token)
    allowed_client_ids = _get_allowed_client_ids()

    audience = str(payload.get("aud", "")).strip()
    if audience not in allowed_client_ids:
        raise ValueError("token audience mismatch")

    issuer = str(payload.get("iss", "")).strip()
    if issuer not in GOOGLE_TOKEN_ISSUERS:
        raise ValueError("token issuer mismatch")

    email = str(payload.get("email", "")).strip().lower()
    if not email:
        raise ValueError("email claim is missing")

    if not _is_email_verified(payload.get("email_verified")):
        raise ValueError("email is not verified")

    return {"email": email}
