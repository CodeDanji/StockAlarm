from __future__ import annotations

import re
from datetime import datetime, timezone

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.alert_rule import AlertRule
from app.models.rule_state import RuleState
from app.services.eodhd_client import EODHDClient
from app.services.evaluator_service import decide_trigger

PRICE_CROSS_ABOVE_PATTERN = re.compile(
    r'price_crosses_above\(\s*symbol="([^"]+)"\s*,\s*ma=(\d+)\s*,\s*timeframe="([^"]+)"\s*\)'
)
RSI_BELOW_PATTERN = re.compile(
    r'rsi_below\(\s*symbol="([^"]+)"\s*,\s*period=(\d+)\s*,\s*threshold=([0-9.]+)\s*,\s*timeframe="([^"]+)"\s*\)'
)


def _fetch_close_series(*, symbol: str, timeframe: str, limit: int) -> list[float]:
    client = EODHDClient()
    try:
        return client.fetch_intraday_close_series(symbol=symbol, interval=timeframe, limit=limit)
    finally:
        client.close()


def _compute_sma(closes: list[float], period: int) -> float:
    if len(closes) < period:
        raise ValueError("not enough close data for sma")
    return sum(closes[-period:]) / period


def _compute_rsi(closes: list[float], period: int) -> float:
    if len(closes) < period + 1:
        raise ValueError("not enough close data for rsi")

    gains = 0.0
    losses = 0.0
    recent = closes[-(period + 1) :]
    for idx in range(1, len(recent)):
        delta = recent[idx] - recent[idx - 1]
        if delta > 0:
            gains += delta
        else:
            losses -= delta

    average_gain = gains / period
    average_loss = losses / period
    if average_loss == 0:
        return 100.0

    rs = average_gain / average_loss
    return 100.0 - (100.0 / (1.0 + rs))


def _evaluate_condition(condition_dsl: str) -> bool | None:
    cross_match = PRICE_CROSS_ABOVE_PATTERN.fullmatch(condition_dsl.strip())
    if cross_match:
        symbol, ma_period_text, timeframe = cross_match.groups()
        ma_period = int(ma_period_text)
        closes = _fetch_close_series(symbol=symbol, timeframe=timeframe, limit=ma_period + 1)
        sma = _compute_sma(closes, ma_period)
        return closes[-1] > sma

    rsi_match = RSI_BELOW_PATTERN.fullmatch(condition_dsl.strip())
    if rsi_match:
        symbol, period_text, threshold_text, timeframe = rsi_match.groups()
        period = int(period_text)
        threshold = float(threshold_text)
        closes = _fetch_close_series(symbol=symbol, timeframe=timeframe, limit=period + 1)
        rsi_value = _compute_rsi(closes, period)
        return rsi_value < threshold

    return None


def run_evaluation_cycle(scope: str) -> dict:
    market_hours = scope == "market_hours"
    evaluated_count = 0
    triggered_count = 0
    unsupported_count = 0
    failed_rule_ids: list[int] = []
    now = datetime.now(timezone.utc)

    with SessionLocal() as db:
        active_rules = db.scalars(select(AlertRule).where(AlertRule.active.is_(True))).all()
        for rule in active_rules:
            try:
                condition_true = _evaluate_condition(rule.condition_dsl)
                if condition_true is None:
                    unsupported_count += 1
                    continue

                state = db.get(RuleState, rule.id)
                if state is None:
                    state = RuleState(rule_id=rule.id, last_state_bool=None, last_trigger_at=None)
                    db.add(state)
                    db.flush()

                should_trigger = decide_trigger(
                    mode=rule.mode,
                    is_true=condition_true,
                    last_state=state.last_state_bool,
                    last_trigger_at=state.last_trigger_at,
                    cooldown_minutes=rule.cooldown_minutes_market,
                    now=now,
                    market_hours=market_hours,
                    off_hours_enabled=False,
                )

                state.last_state_bool = condition_true
                if should_trigger:
                    state.last_trigger_at = now
                    triggered_count += 1
                evaluated_count += 1
            except Exception:  # noqa: BLE001
                failed_rule_ids.append(rule.id)

        db.commit()

    return {
        "scope": scope,
        "status": "ok",
        "evaluated_count": evaluated_count,
        "triggered_count": triggered_count,
        "unsupported_count": unsupported_count,
        "failed_rule_ids": failed_rule_ids,
    }
