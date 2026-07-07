from __future__ import annotations

import logging
from time import perf_counter

from rate_agent.config import Settings
from rate_agent.formatter import format_rate_message
from rate_agent.mppx_rate_client import MppxRateClient
from rate_agent.rate_client import RateClient
from rate_agent.telegram_client import TelegramClient
from rate_agent.tempo_client import TempoRequestClient
from rate_agent.timing import timed_step

logger = logging.getLogger(__name__)


def run(settings: Settings) -> None:
    started_at = perf_counter()
    logger.info(
        "Rate Agent started pair=%s/%s rate_payment_mode=%s source=%s",
        settings.base_currency,
        settings.quote_currency,
        settings.rate_payment_mode,
        settings.rate_source,
    )

    tempo = None
    if settings.rate_payment_mode == "cli":
        tempo = TempoRequestClient(
            tempo_bin=settings.tempo_bin,
            max_spend_usd=settings.mpp_max_spend_usd,
        )
        with timed_step(logger, "check Tempo Wallet"):
            tempo.check_wallet_ready()

    if settings.rate_payment_mode == "mppx":
        rate_client = MppxRateClient(
            helper_dir=settings.mppx_helper_dir,
            timeout_seconds=settings.mppx_command_timeout_seconds,
        )
        with timed_step(logger, "fetch Alpha Vantage rates via mppx"):
            snapshot = rate_client.get_snapshot(
                base_currency=settings.base_currency,
                quote_currency=settings.quote_currency,
            )
    else:
        if tempo is None:
            raise RuntimeError("Tempo client was not initialized for CLI rate mode")
        rate_client = RateClient(tempo=tempo, base_url=settings.rate_base_url)
        with timed_step(logger, "fetch Alpha Vantage rates via Tempo CLI"):
            snapshot = rate_client.get_snapshot(
                base_currency=settings.base_currency,
                quote_currency=settings.quote_currency,
            )

    with timed_step(logger, "format Telegram message"):
        message = format_rate_message(snapshot, timezone=settings.timezone)

    with timed_step(logger, "send Telegram notification"):
        TelegramClient(
            bot_token=settings.telegram_bot_token,
            chat_id=settings.telegram_chat_id,
        ).send_message(message)

    elapsed_ms = (perf_counter() - started_at) * 1000
    logger.info("Rate Agent completed duration_ms=%.2f", elapsed_ms)
