from __future__ import annotations

from datetime import datetime, time


def _parse_hhmm(value: str) -> time:
    hour_str, minute_str = value.split(":")
    return time(hour=int(hour_str), minute=int(minute_str))


def is_quiet_hours(start_hhmm: str, end_hhmm: str, local_dt: datetime) -> bool:
    start = _parse_hhmm(start_hhmm)
    end = _parse_hhmm(end_hhmm)
    now_time = local_dt.time()

    if start <= end:
        return start <= now_time < end
    return now_time >= start or now_time < end


def select_digest_events(events: list[dict]) -> list[dict]:
    return [event for event in events if event.get("suppressed_by_quiet_hours") is True]
