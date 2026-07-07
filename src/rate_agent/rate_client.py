from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from rate_agent.tempo_client import TempoRequestClient


class RateDataError(RuntimeError):
    """Raised when rate data is missing or malformed."""


def redact_helper_output(output: str, limit: int = 6000) -> str:
    import re

    redacted = re.sub(r"(api\.telegram\.org/bot)[^/\s\"']+", r"\1<redacted>", output)
    redacted = re.sub(r"(code=)[^&\s\"']+", r"\1<redacted>", redacted)
    redacted = re.sub(r"0x[a-fA-F0-9]{40}", "<redacted-address>", redacted)
    if len(redacted) > limit:
        return f"{redacted[:limit]}...<truncated>"
    return redacted


@dataclass(frozen=True)
class RateQuote:
    label: str
    value: str
    unit: str
    source_time: str | None = None


@dataclass(frozen=True)
class RateSnapshot:
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


@dataclass(frozen=True)
class RateClient:
    tempo: TempoRequestClient
    base_url: str

    def get_snapshot(self, base_currency: str, quote_currency: str) -> RateSnapshot:
        currency_payload = self.tempo.post_json(
            f"{self.base_url}/alphavantage/currency-exchange-rate",
            {
                "from_currency": base_currency,
                "to_currency": quote_currency,
            },
        )
        return RateSnapshot(
            usd_vnd=parse_currency_quote(currency_payload, label=f"{base_currency}/{quote_currency}"),
        )
