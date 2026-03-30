from fastapi.testclient import TestClient

from app.db.session import engine
from app.main import app
from app.models.base import Base


def test_google_token_login_and_preferences_patch(monkeypatch) -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    monkeypatch.setattr(
        "app.services.google_auth.verify_google_id_token",
        lambda _: {"email": "user@example.com"},
    )

    client = TestClient(app)

    login = client.post("/auth/google/token", json={"id_token": "good-token"})
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = client.get("/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "user@example.com"

    patch = client.patch(
        "/me/preferences",
        json={
            "timezone": "America/New_York",
            "quiet_hours_start": "22:00",
            "quiet_hours_end": "06:00",
        },
        headers={"Authorization": f"Bearer {token}"},
    )
    assert patch.status_code == 200
    body = patch.json()
    assert body["timezone"] == "America/New_York"
    assert body["quiet_hours_start"] == "22:00"
    assert body["quiet_hours_end"] == "06:00"
