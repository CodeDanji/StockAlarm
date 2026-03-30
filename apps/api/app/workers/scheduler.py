from __future__ import annotations


def build_jobs() -> list[dict]:
    return [
        {"name": "ingest-15m-market-hours", "cron": "*/15 * * * 1-5"},
        {"name": "evaluate-15m-market-hours", "cron": "*/15 * * * 1-5"},
        {"name": "ingest-1h-off-hours", "cron": "0 * * * *"},
        {"name": "evaluate-1h-off-hours", "cron": "0 * * * *"},
        {"name": "digest-morning", "cron": "0 7 * * *"},
    ]
