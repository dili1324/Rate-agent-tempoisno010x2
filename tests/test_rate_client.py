from typing import Any

import pytest

from rate_agent.rate_client import (
    RateClient,
    RateDataError,
    parse_currency_quote,
    parse_gold_quote,
    redact_helper_output,
)


class FakeTempo:
    def __init__(self, responses: list[Any]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def post_json(self, url: str, payload: dict[str, Any]) -> Any:
        self.calls.append((url, payload))
        return self.responses.pop(0)


def test_parse_currency_quote_accepts_alpha_vantage_realtime_shape() -> None:
    quote = parse_currency_quote(
        {
            "Realtime Currency Exchange Rate": {
                "1. From_Currency Code": "USD",
                "3. To_Currency Code": "VND",
                "5. Exchange Rate": "25234.1234",
                "6. Last Refreshed": "2026-07-07 00:00:00",
            }
        }
    )

    assert quote.label == "USD/VND"
    assert quote.value == "25234.1234"
    assert quote.source_time == "2026-07-07 00:00:00"


def test_parse_gold_quote_accepts_locus_data_series_wrapper() -> None:
    quote = parse_gold_quote(
        {
            "success": True,
            "data": {
                "name": "Gold spot",
                "data": [{"date": "2026-07-07", "value": "2035.42"}],
            },
        }
    )

    assert quote.label == "XAU/USD"
    assert quote.value == "2035.42"
    assert quote.source_time == "2026-07-07"


def test_rate_client_calls_alpha_vantage_endpoints() -> None:
    tempo = FakeTempo(
        [
            {"data": {"data": [{"date": "2026-07-07", "value": "2035.42"}]}},
            {"Realtime Currency Exchange Rate": {"5. Exchange Rate": "25234.1234"}},
        ]
    )
    client = RateClient(tempo=tempo, base_url="https://example.test")  # type: ignore[arg-type]

    snapshot = client.get_snapshot(metal_symbol="XAU", base_currency="USD", quote_currency="VND")

    assert snapshot.gold.value == "2035.42"
    assert snapshot.usd_vnd.value == "25234.1234"
    assert tempo.calls[0][0].endswith("/alphavantage/currency-exchange-rate")
    assert tempo.calls[0][1] == {"from_currency": "XAU", "to_currency": "USD"}
    assert tempo.calls[1][0].endswith("/alphavantage/currency-exchange-rate")
    assert tempo.calls[1][1] == {"from_currency": "USD", "to_currency": "VND"}


def test_parse_currency_quote_rejects_missing_rate() -> None:
    with pytest.raises(RateDataError):
        parse_currency_quote({"Realtime Currency Exchange Rate": {}})


def test_redact_helper_output_hides_addresses_and_auth_codes() -> None:
    output = (
        "wallet=0xeDC42cA9000D7001f967b7bb51872af9f4E636c6 "
        "url=https://wallet.tempo.xyz/api/auth/cli?code=SECRET"
    )

    redacted = redact_helper_output(output)

    assert "0xeDC42cA9000D7001f967b7bb51872af9f4E636c6" not in redacted
    assert "SECRET" not in redacted
    assert "<redacted-address>" in redacted
    assert "code=<redacted>" in redacted
