from rate_agent.formatter import format_rate_message
from rate_agent.rate_client import RateQuote, RateSnapshot


def test_format_rate_message_contains_core_fields() -> None:
    snapshot = RateSnapshot(
        gold=RateQuote(label="XAU/USD", value="2035.42", unit="USD per troy oz", source_time="2026-07-07"),
        usd_vnd=RateQuote(label="USD/VND", value="25234.0000", unit="VND per USD", source_time="2026-07-07 00:00:00"),
    )

    message = format_rate_message(snapshot)

    assert "Rate Agent - cập nhật 07:30 GMT+7" in message
    assert "XAU/USD: 2035.42" in message
    assert "USD/VND: 25234" in message
    assert "Nguồn: Alpha Vantage via MPP" in message
    assert "Thời gian dữ liệu:" in message
