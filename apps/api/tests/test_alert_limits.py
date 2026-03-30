from fastapi.testclient import TestClient

from app.db.session import engine
from app.main import app
from app.models.base import Base


def test_free_plan_blocks_fourth_alert(monkeypatch) -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    monkeypatch.setattr(
        "app.services.google_auth.verify_google_id_token",
        lambda _: {"email": "limit@example.com"},
    )

    client = TestClient(app)
    token = client.post("/auth/google/token", json={"id_token": "ok"}).json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    for idx in range(3):
        ok = client.post(
            "/alerts",
            json={
                "name": f"a-{idx}",
                "condition_dsl": 'price_crosses_above(symbol="AAPL", ma=20, timeframe="15m")',
                "mode": "A",
                "cooldown_minutes_market": 120,
                "active": True,
            },
            headers=headers,
        )
        assert ok.status_code == 201

    blocked = client.post(
        "/alerts",
        json={
            "name": "a-3",
            "condition_dsl": 'rsi_below(symbol="AAPL", period=14, threshold=30, timeframe="15m")',
            "mode": "A",
            "cooldown_minutes_market": 120,
            "active": True,
        },
        headers=headers,
    )
    assert blocked.status_code == 402
