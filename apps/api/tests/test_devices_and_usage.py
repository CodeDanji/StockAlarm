from fastapi.testclient import TestClient

from app.db.session import engine
from app.main import app
from app.models.base import Base


def test_device_registration_and_usage_endpoint(monkeypatch) -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    monkeypatch.setattr(
        "app.services.google_auth.verify_google_id_token",
        lambda _: {"email": "device@example.com"},
    )

    client = TestClient(app)
    token = client.post("/auth/google/token", json={"id_token": "ok"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    device = client.post(
        "/devices/register",
        json={"fcm_token": "tok-1", "platform": "web"},
        headers=headers,
    )
    assert device.status_code == 201

    usage = client.get("/billing/usage", headers=headers)
    assert usage.status_code == 200
    assert usage.json()["plan_tier"] == "free"
