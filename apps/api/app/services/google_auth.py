from __future__ import annotations


def verify_google_id_token(id_token: str) -> dict[str, str]:
    if not id_token:
        raise ValueError("invalid token")
    return {"email": "sample@example.com"}
