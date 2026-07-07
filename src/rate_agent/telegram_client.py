from __future__ import annotations

import json
import logging
import urllib.error
import urllib.request
from dataclasses import dataclass

logger = logging.getLogger(__name__)


class TelegramError(RuntimeError):
    """Raised when Telegram rejects the notification."""


def _mask_chat_id(chat_id: str) -> str:
    if len(chat_id) <= 4:
        return "****"
    return f"{chat_id[:2]}***{chat_id[-2:]}"


@dataclass(frozen=True)
class TelegramClient:
    bot_token: str
    chat_id: str

    def send_message(self, text: str) -> None:
        masked_chat_id = _mask_chat_id(self.chat_id)
        logger.info("Sending Telegram message chat_id=%s text_length=%d", masked_chat_id, len(text))
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "disable_web_page_preview": True,
        }
        data = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            url,
            data=data,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(request, timeout=20) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise TelegramError(f"Telegram API returned HTTP {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise TelegramError(f"Telegram API request failed: {exc.reason}") from exc

        if not body.get("ok"):
            raise TelegramError("Telegram API returned ok=false")
        logger.info("Telegram message sent chat_id=%s", masked_chat_id)
