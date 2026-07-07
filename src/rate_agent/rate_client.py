from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rate_agent.tempo_client import TempoRequestClient


class RateDataError(RuntimeError):
    """Raised when rate data is missing or malformed."""


@dataclass(frozen=True)
class RateQuote:
    label: str
    value: str
    unit: str
    source_time: str | None = None


@dataclass(frozen=True)
class RateSnapshot:
    gold: RateQuote
    usd_vnd: RateQuote
    source: str = "Alpha Vantage via MPP"


def _unwrap_payload(value: Any) -> Any:
    while isinstance(value, dict):
        if "data" in value and len(value) <= 3:
            value = value["data"]
            continue
        if "result" in value and len(value) <= 3:
            value = value["result"]
            continue
        if "body" in value and len(value) <= 3:
            value = value["body"]
            continue
        return value
    return value


def _first_string(mapping: dict[str, Any], keys: tuple[str, ...]) -> str | None:
    lowered = {key.lower(): value for key, value in mapping.items()}
    for key in keys:
        value = lowered.get(key.lower())
        if value is None:
            continue
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return None


def _latest_series_point(payload: Any) -> tuple[str, str] | None:
    data = _unwrap_payload(payload)
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict):
            value = _first_string(first, ("value", "price", "close", "rate"))
            date = _first_string(first, ("date", "timestamp", "time"))
            if value:
                return value, date or ""

    if isinstance(data, dict):
        series = data.get("data")
        if isinstance(series, list) and series:
            first = series[0]
            if isinstance(first, dict):
                value = _first_string(first, ("value", "price", "close", "rate"))
                date = _first_string(first, ("date", "timestamp", "time"))
                if value:
                    return value, date or ""

        for value in data.values():
            point = _latest_series_point(value)
            if point:
                return point
    return None


def parse_currency_quote(payload: Any, label: str = "USD/VND") -> RateQuote:
    data = _unwrap_payload(payload)
    if not isinstance(data, dict):
        raise RateDataError("Currency exchange response was not a JSON object")

    rate_block = data.get("Realtime Currency Exchange Rate")
    if isinstance(rate_block, dict):
        rate = _first_string(
            rate_block,
            (
                "5. Exchange Rate",
                "exchange_rate",
                "rate",
                "price",
            ),
        )
        source_time = _first_string(
            rate_block,
            (
                "6. Last Refreshed",
                "last_refreshed",
                "timestamp",
                "time",
            ),
        )
        if rate:
            return RateQuote(label=label, value=rate, unit="VND per USD", source_time=source_time)

    rate = _first_string(data, ("exchange_rate", "rate", "price", "value"))
    source_time = _first_string(data, ("last_refreshed", "timestamp", "time", "date"))
    if not rate:
        raise RateDataError("Currency exchange response did not include an exchange rate")
    return RateQuote(label=label, value=rate, unit="VND per USD", source_time=source_time)


def parse_gold_quote(payload: Any, symbol: str = "XAU") -> RateQuote:
    data = _unwrap_payload(payload)
    if isinstance(data, dict):
        rate_block = data.get("Realtime Currency Exchange Rate")
        if isinstance(rate_block, dict):
            rate = _first_string(rate_block, ("5. Exchange Rate", "exchange_rate", "rate", "price"))
            source_time = _first_string(rate_block, ("6. Last Refreshed", "last_refreshed", "time"))
            if rate:
                return RateQuote(label=f"{symbol}/USD", value=rate, unit="USD per troy oz", source_time=source_time)

        direct_rate = _first_string(data, ("price", "value", "rate", "close"))
        source_time = _first_string(data, ("last_refreshed", "timestamp", "time", "date"))
        if direct_rate:
            return RateQuote(label=f"{symbol}/USD", value=direct_rate, unit="USD per troy oz", source_time=source_time)

    series_point = _latest_series_point(data)
    if series_point:
        value, source_time = series_point
        return RateQuote(label=f"{symbol}/USD", value=value, unit="USD per troy oz", source_time=source_time or None)

    raise RateDataError("Gold response did not include a parseable price")


@dataclass(frozen=True)
class RateClient:
    tempo: TempoRequestClient
    base_url: str

    def get_snapshot(self, metal_symbol: str, base_currency: str, quote_currency: str) -> RateSnapshot:
        gold_payload = self.tempo.post_json(
            f"{self.base_url}/alphavantage/commodity-price",
            {
                "commodity": "GOLD_SILVER_SPOT",
                "symbol": metal_symbol,
                "datatype": "json",
            },
        )
        currency_payload = self.tempo.post_json(
            f"{self.base_url}/alphavantage/currency-exchange-rate",
            {
                "from_currency": base_currency,
                "to_currency": quote_currency,
            },
        )
        return RateSnapshot(
            gold=parse_gold_quote(gold_payload, symbol=metal_symbol),
            usd_vnd=parse_currency_quote(currency_payload, label=f"{base_currency}/{quote_currency}"),
        )
