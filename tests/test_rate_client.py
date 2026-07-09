from typing import Any

import pytest

from rate_agent.rate_client import (
    RateClient,
    RateDataError,
    parse_currency_quote,
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


def test_rate_client_calls_alpha_vantage_endpoints() -> None:
    tempo = FakeTempo(
        [
            {"Realtime Currency Exchange Rate": {"5. Exchange Rate": "25234.1234"}},
        ]
    )
    client = RateClient(tempo=tempo, base_url="https://example.test")  # type: ignore[arg-type]

    snapshot = client.get_snapshot(base_currency="USD", quote_currency="VND")

    assert snapshot.usd_vnd.value == "25234.1234"
    assert tempo.calls[0][0].endswith("/alphavantage/currency-exchange-rate")
    assert tempo.calls[0][1] == {"from_currency": "USD", "to_currency": "VND"}
    assert len(tempo.calls) == 1


def test_parse_currency_quote_rejects_missing_rate() -> None:
    with pytest.raises(RateDataError):
        parse_currency_quote({"Realtime Currency Exchange Rate": {}})


def test_redact_helper_output_hides_addresses_and_auth_codes() -> None:
    output = (
        "wallet=0x1111111111111111111111111111111111111111 "
        "url=https://wallet.tempo.xyz/api/auth/cli?code=SECRET"
    )

    redacted = redact_helper_output(output)

    assert "0x1111111111111111111111111111111111111111" not in redacted
    assert "SECRET" not in redacted
    assert "<redacted-address>" in redacted
    assert "code=<redacted>" in redacted
