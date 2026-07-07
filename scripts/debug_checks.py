from __future__ import annotations

import argparse
import logging
import os
import sys

from rate_agent.config import Settings
from rate_agent.logging_config import configure_logging
from rate_agent.rate_client import RateClient
from rate_agent.telegram_client import TelegramClient
from rate_agent.tempo_client import TempoRequestClient


def _tempo_from_env() -> TempoRequestClient:
    return TempoRequestClient(
        tempo_bin=os.getenv("TEMPO_BIN", "tempo"),
        max_spend_usd=os.getenv("MPP_MAX_SPEND_USD", "0.05"),
    )


def check_tempo() -> None:
    _tempo_from_env().check_wallet_ready()


def check_rate() -> None:
    tempo = _tempo_from_env()
    client = RateClient(
        tempo=tempo,
        base_url=os.getenv(
            "ALPHAVANTAGE_MPP_BASE_URL",
            "https://alphavantage.mpp.paywithlocus.com",
        ).rstrip("/"),
    )
    snapshot = client.get_snapshot(
        base_currency=os.getenv("BASE_CURRENCY", "USD"),
        quote_currency=os.getenv("QUOTE_CURRENCY", "VND"),
    )
    logging.info("Rate check OK usd_vnd=%s", snapshot.usd_vnd.value)


def check_telegram() -> None:
    settings = Settings.from_env()
    TelegramClient(
        bot_token=settings.telegram_bot_token,
        chat_id=settings.telegram_chat_id,
    ).send_message("Rate Agent debug check: Telegram is working.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MVP debug checks for Rate Agent.")
    parser.add_argument(
        "check",
        choices=["tempo", "rate", "telegram", "all"],
        help="Which integration to check.",
    )
    args = parser.parse_args()

    configure_logging()
    try:
        if args.check in {"tempo", "all"}:
            check_tempo()
        if args.check in {"rate", "all"}:
            check_rate()
        if args.check in {"telegram", "all"}:
            check_telegram()
    except Exception:
        logging.exception("Debug check failed")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
