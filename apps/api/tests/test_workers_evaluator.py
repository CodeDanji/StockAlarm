from __future__ import annotations

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker

from app.models.alert_rule import AlertRule
from app.models.base import Base
from app.models.rule_state import RuleState
from app.models.user import User
from app.workers import evaluator


def test_run_evaluation_cycle_mode_a_triggers_only_once(monkeypatch) -> None:
    engine = create_engine("sqlite+pysqlite:///:memory:", future=True)
    local_session = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    Base.metadata.create_all(engine)

    with Session(engine) as session:
        user = User(
            email="eval@example.com",
            plan_tier="free",
            timezone="Asia/Seoul",
            quiet_hours_start="23:00",
            quiet_hours_end="07:00",
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        rule = AlertRule(
            user_id=user.id,
            name="aapl-ma-cross",
            condition_dsl='price_crosses_above(symbol="AAPL", ma=3, timeframe="15m")',
            mode="A",
            cooldown_minutes_market=120,
            active=True,
        )
        session.add(rule)
        session.commit()

    monkeypatch.setattr(evaluator, "SessionLocal", local_session)
    monkeypatch.setattr(evaluator, "_fetch_close_series", lambda **_: [10.0, 11.0, 12.0])

    first = evaluator.run_evaluation_cycle("market_hours")
    second = evaluator.run_evaluation_cycle("market_hours")

    assert first["evaluated_count"] == 1
    assert first["triggered_count"] == 1
    assert second["evaluated_count"] == 1
    assert second["triggered_count"] == 0

    with Session(engine) as session:
        state = session.scalar(select(RuleState).where(RuleState.rule_id == 1))
        assert state is not None
        assert state.last_state_bool is True
        assert state.last_trigger_at is not None
