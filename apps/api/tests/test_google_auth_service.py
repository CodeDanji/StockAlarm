from __future__ import annotations

import pytest

from app.services import google_auth


def test_verify_google_id_token_rejects_empty_token() -> None:
    with pytest.raises(ValueError, match="invalid token"):
        google_auth.verify_google_id_token("")


def test_verify_google_id_token_requires_client_id_config(monkeypatch) -> None:
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.delenv("GOOGLE_CLIENT_IDS", raising=False)
    monkeypatch.setattr(
        google_auth,
        "_verify_with_google",
        lambda _: {
            "aud": "client-1",
            "iss": "https://accounts.google.com",
            "email": "user@example.com",
            "email_verified": True,
        },
    )

    with pytest.raises(ValueError, match="client id"):
        google_auth.verify_google_id_token("token")


def test_verify_google_id_token_returns_normalized_email(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "client-1")
    monkeypatch.delenv("GOOGLE_CLIENT_IDS", raising=False)
    monkeypatch.setattr(
        google_auth,
        "_verify_with_google",
        lambda _: {
            "aud": "client-1",
            "iss": "https://accounts.google.com",
            "email": "USER@example.com",
            "email_verified": "true",
        },
    )

    assert google_auth.verify_google_id_token("token") == {"email": "user@example.com"}


def test_verify_google_id_token_rejects_audience_mismatch(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_CLIENT_IDS", "client-1,client-2")
    monkeypatch.delenv("GOOGLE_CLIENT_ID", raising=False)
    monkeypatch.setattr(
        google_auth,
        "_verify_with_google",
        lambda _: {
            "aud": "other-client",
            "iss": "https://accounts.google.com",
            "email": "user@example.com",
            "email_verified": True,
        },
    )

    with pytest.raises(ValueError, match="audience"):
        google_auth.verify_google_id_token("token")


def test_verify_google_id_token_rejects_unverified_email(monkeypatch) -> None:
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "client-1")
    monkeypatch.delenv("GOOGLE_CLIENT_IDS", raising=False)
    monkeypatch.setattr(
        google_auth,
        "_verify_with_google",
        lambda _: {
            "aud": "client-1",
            "iss": "https://accounts.google.com",
            "email": "user@example.com",
            "email_verified": False,
        },
    )

    with pytest.raises(ValueError, match="verified"):
        google_auth.verify_google_id_token("token")
