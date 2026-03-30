from __future__ import annotations

import re


def generate_candidates(*, prompt: str, model: str) -> list[dict]:
    del prompt
    del model
    return [
        {
            "title": "MA20 Breakout",
            "condition_dsl": 'price_crosses_above(symbol="AAPL", ma=20, timeframe="15m")',
        }
    ]


def _has_unresolved_symbol(condition_dsl: str) -> bool:
    match = re.search(r'symbol="([^"]+)"', condition_dsl)
    if match is None:
        return True
    symbol = match.group(1).strip().upper()
    return symbol in {"", "UNKNOWN", "UNRESOLVED", "?"}


def generate_strategies(idea: str) -> tuple[list[dict], str]:
    mini_candidates = generate_candidates(prompt=idea, model="gpt-5.4-mini")
    if any(_has_unresolved_symbol(item["condition_dsl"]) for item in mini_candidates):
        return generate_candidates(prompt=idea, model="gpt-5.4"), "gpt-5.4"
    return mini_candidates, "gpt-5.4-mini"
