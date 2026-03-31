from __future__ import annotations

from app.services.eodhd_client import EODHDClient


class _FakeResponse:
    def __init__(self, payload: object) -> None:
        self._payload = payload

    def raise_for_status(self) -> None:
        return None

    def json(self) -> object:
        return self._payload


class _FakeHTTPClient:
    def __init__(self, payload: object) -> None:
        self.payload = payload
        self.calls: list[tuple[str, dict]] = []

    def get(self, url: str, params: dict) -> _FakeResponse:
        self.calls.append((url, params))
        return _FakeResponse(self.payload)


def test_normalize_symbol_defaults() -> None:
    assert EODHDClient.normalize_symbol("aapl") == "AAPL.US"
    assert EODHDClient.normalize_symbol("005930") == "005930.KS"
    assert EODHDClient.normalize_symbol("SPY.US") == "SPY.US"


def test_fetch_intraday_close_series_sorts_and_parses() -> None:
    fake = _FakeHTTPClient(
        [
            {"datetime": "2026-03-31 09:15:00", "close": 101.0},
            {"datetime": "2026-03-31 09:00:00", "close": 100.5},
            {"timestamp": 1774949400, "close": 101.5},
        ]
    )

    client = EODHDClient(api_key="test-key", http_client=fake)
    closes = client.fetch_intraday_close_series(symbol="AAPL", interval="15m", limit=3)

    assert closes == [100.5, 101.0, 101.5]
    assert fake.calls
    url, params = fake.calls[0]
    assert "/intraday/AAPL.US" in url
    assert params["interval"] == "15m"
    assert params["limit"] == 3
