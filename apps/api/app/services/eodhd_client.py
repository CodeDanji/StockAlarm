from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx


@dataclass(frozen=True)
class IntradayClosePoint:
    symbol: str
    close: float
    as_of_utc: datetime


class EODHDClient:
    API_BASE_URL = "https://eodhd.com/api"

    def __init__(self, *, api_key: str | None = None, http_client: Any | None = None) -> None:
        key = (api_key or os.getenv("EODHD_API_KEY", "")).strip()
        if not key:
            raise ValueError("EODHD_API_KEY is not configured")

        self.api_key = key
        self.http_client = http_client or httpx.Client(timeout=10.0)
        self._owns_http_client = http_client is None

    def close(self) -> None:
        if self._owns_http_client:
            self.http_client.close()

    @staticmethod
    def normalize_symbol(symbol: str) -> str:
        raw = symbol.strip().upper()
        if "." in raw:
            return raw
        if raw.isdigit() and len(raw) == 6:
            return f"{raw}.KS"
        return f"{raw}.US"

    @staticmethod
    def _parse_as_of_utc(bar: dict[str, Any]) -> datetime:
        if "timestamp" in bar and bar["timestamp"] is not None:
            return datetime.fromtimestamp(int(bar["timestamp"]), tz=timezone.utc)

        if "datetime" in bar and bar["datetime"]:
            value = str(bar["datetime"]).strip()
            try:
                dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                dt = datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)

        raise ValueError("intraday bar timestamp is missing")

    @staticmethod
    def _extract_bars(payload: Any) -> list[dict[str, Any]]:
        if isinstance(payload, list):
            return [item for item in payload if isinstance(item, dict)]
        if isinstance(payload, dict):
            data = payload.get("data")
            if isinstance(data, list):
                return [item for item in data if isinstance(item, dict)]
        return []

    def fetch_intraday_points(self, *, symbol: str, interval: str, limit: int) -> list[IntradayClosePoint]:
        normalized_symbol = self.normalize_symbol(symbol)
        response = self.http_client.get(
            f"{self.API_BASE_URL}/intraday/{normalized_symbol}",
            params={
                "api_token": self.api_key,
                "fmt": "json",
                "interval": interval,
                "limit": limit,
            },
        )
        response.raise_for_status()
        payload = response.json()
        bars = self._extract_bars(payload)
        if not bars:
            raise ValueError(f"no intraday data returned for {normalized_symbol}")

        points: list[IntradayClosePoint] = []
        for bar in bars:
            if bar.get("close") is None:
                continue
            points.append(
                IntradayClosePoint(
                    symbol=normalized_symbol,
                    close=float(bar["close"]),
                    as_of_utc=self._parse_as_of_utc(bar),
                )
            )

        if not points:
            raise ValueError(f"intraday close values are missing for {normalized_symbol}")

        points.sort(key=lambda item: item.as_of_utc)
        return points

    def fetch_intraday_close_series(self, *, symbol: str, interval: str, limit: int) -> list[float]:
        points = self.fetch_intraday_points(symbol=symbol, interval=interval, limit=limit)
        return [point.close for point in points]

    def fetch_latest_intraday_close(self, *, symbol: str, interval: str) -> IntradayClosePoint:
        points = self.fetch_intraday_points(symbol=symbol, interval=interval, limit=1)
        return points[-1]
