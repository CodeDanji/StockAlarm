from datetime import datetime, timedelta, timezone

from app.services.evaluator_service import decide_trigger


def test_mode_a_transition_only() -> None:
    now = datetime.now(timezone.utc)
    assert decide_trigger(
        mode="A",
        is_true=True,
        last_state=False,
        last_trigger_at=None,
        cooldown_minutes=120,
        now=now,
        market_hours=True,
    )
    assert not decide_trigger(
        mode="A",
        is_true=True,
        last_state=True,
        last_trigger_at=now,
        cooldown_minutes=120,
        now=now + timedelta(minutes=15),
        market_hours=True,
    )


def test_mode_b_market_cooldown() -> None:
    now = datetime.now(timezone.utc)
    assert decide_trigger(
        mode="B",
        is_true=True,
        last_state=True,
        last_trigger_at=now - timedelta(minutes=130),
        cooldown_minutes=120,
        now=now,
        market_hours=True,
    )
    assert not decide_trigger(
        mode="B",
        is_true=True,
        last_state=True,
        last_trigger_at=now - timedelta(minutes=30),
        cooldown_minutes=120,
        now=now,
        market_hours=True,
    )


def test_offhours_default_off() -> None:
    now = datetime.now(timezone.utc)
    assert not decide_trigger(
        mode="B",
        is_true=True,
        last_state=False,
        last_trigger_at=None,
        cooldown_minutes=120,
        now=now,
        market_hours=False,
        off_hours_enabled=False,
    )
