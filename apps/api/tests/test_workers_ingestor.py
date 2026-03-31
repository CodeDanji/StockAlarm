from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.models.alert_rule import AlertRule
from app.models.base import Base
from app.models.market_snapshot import MarketSnapshot
from app.models.user import User
from app.services.eodhd_client import IntradayClosePoint
from app.workers import ingestor


class _FakeEODHDClient:
    def __init__(self, *, api_key: str | None = None) -> None:
        del api_key

    def fetch_latest_intraday_close(self, *, symbol: str, interval: str) -> IntradayClosePoint:
        del interval
        normalized = symbol if "." in symbol else f"{symbol}.US"
        return IntradayClosePoint(
            symbol=normalized,
            close=123.45 if normalized.startswith("AAPL") else 70000.0,
            as_of_utc=datetime(2026, 3, 31, 9, 15, tzinfo=timezone.utc),
        )

    def close(self) -> None:
        return None


def test_run_ingestion_cycle_persists_market_snapshots(monkeypatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    local_session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        user = User(
            email="ingestor@example.com",
            plan_tier="free",
            timezone="Asia/Seoul",
            quiet_hours_start="23:00",
            quiet_hours_end="07:00",
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        session.add_all(
            [
                AlertRule(
                    user_id=user.id,
                    name="aapl-rsi",
                    condition_dsl='rsi_below(symbol="AAPL", period=14, threshold=30, timeframe="15m")',
                    mode="A",
                    cooldown_minutes_market=120,
                    active=True,
                ),
                AlertRule(
                    user_id=user.id,
                    name="samsung-rsi",
                    condition_dsl='rsi_below(symbol="005930.KS", period=14, threshold=30, timeframe="15m")',
                    mode="A",
                    cooldown_minutes_market=120,
                    active=True,
                ),
            ]
        )
        session.commit()

    monkeypatch.setattr(ingestor, "SessionLocal", local_session)
    monkeypatch.setattr(ingestor, "EODHDClient", _FakeEODHDClient)

    result = ingestor.run_ingestion_cycle("market_hours")

    assert result["status"] == "ok"
    assert result["symbol_count"] == 2
    assert result["updated_count"] == 2
    assert result["failed_symbols"] == []

    with Session(engine) as session:
        rows = session.scalars(select(MarketSnapshot)).all()
        assert len(rows) == 2
        symbols = {row.symbol for row in rows}
        assert symbols == {"AAPL.US", "005930.KS"}
