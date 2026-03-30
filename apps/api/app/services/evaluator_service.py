from __future__ import annotations

from datetime import datetime, timedelta


def decide_trigger(
    *,
    mode: str,
    is_true: bool,
    last_state: bool | None,
    last_trigger_at: datetime | None,
    cooldown_minutes: int,
    now: datetime,
    market_hours: bool,
    off_hours_enabled: bool = False,
) -> bool:
    if not is_true:
        return False

    if not market_hours and not off_hours_enabled:
        return False

    normalized_mode = mode.upper()

    if normalized_mode == "A":
        return last_state in {False, None}

    if normalized_mode == "B":
        effective_cooldown = cooldown_minutes if market_hours else 360
        if last_trigger_at is None:
            return True
        return now >= last_trigger_at + timedelta(minutes=effective_cooldown)

    return False
