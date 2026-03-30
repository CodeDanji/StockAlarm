from datetime import datetime

from app.services.notification_policy import is_quiet_hours, select_digest_events


def test_quiet_hours_detection() -> None:
    assert is_quiet_hours("23:00", "07:00", datetime.fromisoformat("2026-03-30T23:30:00"))
    assert not is_quiet_hours(
        "23:00",
        "07:00",
        datetime.fromisoformat("2026-03-30T10:30:00"),
    )


def test_digest_selects_only_suppressed_events() -> None:
    events = [
        {"id": 1, "suppressed_by_quiet_hours": True},
        {"id": 2, "suppressed_by_quiet_hours": False},
    ]
    assert [e["id"] for e in select_digest_events(events)] == [1]
