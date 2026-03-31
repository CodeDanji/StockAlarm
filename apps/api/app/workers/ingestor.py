from __future__ import annotations

import re
from datetime import datetime, timezone

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.alert_rule import AlertRule
from app.models.market_snapshot import MarketSnapshot
from app.services.eodhd_client import EODHDClient

SYMBOL_PATTERN = re.compile(r'symbol="([^"]+)"')


def _extract_symbols(condition_dsl_values: list[str]) -> list[str]:
    symbols: set[str] = set()
    for condition_dsl in condition_dsl_values:
        for match in SYMBOL_PATTERN.findall(condition_dsl):
            symbols.add(match.strip().upper())
    return sorted(symbols)


def _interval_for_scope(scope: str) -> tuple[str, int]:
    if scope == "off_hours":
        return "1h", 60
    return "15m", 15


def run_ingestion_cycle(scope: str) -> dict:
    interval, delay_minutes = _interval_for_scope(scope)

    with SessionLocal() as db:
        active_rules = db.scalars(select(AlertRule).where(AlertRule.active.is_(True))).all()
        symbols = _extract_symbols([rule.condition_dsl for rule in active_rules])

        if not symbols:
            return {
                "scope": scope,
                "status": "ok",
                "symbol_count": 0,
                "updated_count": 0,
                "failed_symbols": [],
            }

        updated_count = 0
        failed_symbols: list[str] = []
        client = EODHDClient()
        try:
            for symbol in symbols:
                try:
                    point = client.fetch_latest_intraday_close(symbol=symbol, interval=interval)
                    row = db.scalar(select(MarketSnapshot).where(MarketSnapshot.symbol == point.symbol))
                    if row is None:
                        row = MarketSnapshot(
                            symbol=point.symbol,
                            last_price=point.close,
                            source_interval=interval,
                            source_delay_minutes=delay_minutes,
                            as_of_utc=point.as_of_utc,
                            updated_at=datetime.now(timezone.utc),
                        )
                        db.add(row)
                    else:
                        row.last_price = point.close
                        row.source_interval = interval
                        row.source_delay_minutes = delay_minutes
                        row.as_of_utc = point.as_of_utc
                        row.updated_at = datetime.now(timezone.utc)
                    updated_count += 1
                except Exception:  # noqa: BLE001
                    failed_symbols.append(symbol)
            db.commit()
        finally:
            client.close()

    return {
        "scope": scope,
        "status": "ok",
        "symbol_count": len(symbols),
        "updated_count": updated_count,
        "failed_symbols": failed_symbols,
    }
