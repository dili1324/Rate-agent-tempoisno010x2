from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from rate_agent.rate_client import RateQuote, RateSnapshot


def _format_quote(quote: RateQuote) -> str:
    value = quote.value
    if quote.label == "USD/VND":
        value = quote.value.rstrip("0").rstrip(".") if "." in quote.value else quote.value
    return f"{quote.label}: {value} ({quote.unit})"


def _source_time(snapshot: RateSnapshot) -> str:
    times = [quote.source_time for quote in (snapshot.gold, snapshot.usd_vnd) if quote.source_time]
    return " / ".join(times) if times else "không có trong phản hồi"


def format_rate_message(snapshot: RateSnapshot, timezone: str = "Asia/Ho_Chi_Minh") -> str:
    timestamp = datetime.now(ZoneInfo(timezone)).strftime("%Y-%m-%d %H:%M")
    lines = [
        f"Rate Agent - cập nhật 07:30 GMT+7 ({timestamp} {timezone})",
        _format_quote(snapshot.gold),
        _format_quote(snapshot.usd_vnd),
        f"Nguồn: {snapshot.source}",
        f"Thời gian dữ liệu: {_source_time(snapshot)}",
    ]
    return "\n".join(lines)
