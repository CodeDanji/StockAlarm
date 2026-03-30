from fastapi.testclient import TestClient

from app.db.session import engine
from app.main import app
from app.models.base import Base


def test_strategy_generation_escalates_when_symbol_unresolved(monkeypatch) -> None:
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    calls: list[str] = []

    def fake_generate(*, prompt: str, model: str) -> list[dict]:
        calls.append(model)
        if model == "gpt-5.4-mini":
            return [
                {
                    "title": "candidate-mini",
                    "condition_dsl": 'rsi_below(symbol="UNKNOWN", period=14, threshold=30, timeframe="15m")',
                }
            ]
        return [
            {
                "title": "candidate-pro",
                "condition_dsl": 'rsi_below(symbol="AAPL", period=14, threshold=30, timeframe="15m")',
            }
        ]

    monkeypatch.setattr("app.services.strategy_service.generate_candidates", fake_generate)
    monkeypatch.setattr(
        "app.services.google_auth.verify_google_id_token",
        lambda _: {"email": "ai@example.com"},
    )

    client = TestClient(app)
    token = client.post("/auth/google/token", json={"id_token": "ok"}).json()["access_token"]
    res = client.post(
        "/strategies/generate",
        json={"idea": "apple rsi under 30"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert res.status_code == 200
    assert calls == ["gpt-5.4-mini", "gpt-5.4"]
