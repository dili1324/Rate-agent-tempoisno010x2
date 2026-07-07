from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from rate_agent.rate_client import (
    RateDataError,
    RateSnapshot,
    parse_currency_quote,
    parse_gold_quote,
    redact_helper_output,
)

logger = logging.getLogger(__name__)


def _resolve_executable(name: str) -> str:
    resolved = shutil.which(name)
    if resolved:
        return resolved
    if os.path.isabs(name):
        return name
    for candidate in ("/opt/homebrew/bin/npm", "/usr/local/bin/npm"):
        if name == "npm" and Path(candidate).exists():
            return candidate
    return name


@dataclass(frozen=True)
class MppxRateClient:
    helper_dir: str
    timeout_seconds: int
    npm_bin: str = "npm"

    def get_snapshot(self, metal_symbol: str, base_currency: str, quote_currency: str) -> RateSnapshot:
        helper_path = Path(self.helper_dir)
        if not helper_path.exists():
            raise RateDataError(f"MPP helper directory does not exist: {helper_path}")

        env = os.environ.copy()
        npm_bin = _resolve_executable(self.npm_bin)
        env["PATH"] = f"{Path(npm_bin).parent}{os.pathsep}{env.get('PATH', '')}"
        env.update(
            {
                "METAL_SYMBOL": metal_symbol,
                "BASE_CURRENCY": base_currency,
                "QUOTE_CURRENCY": quote_currency,
            }
        )

        logger.info(
            "Calling Node mppx Alpha Vantage helper helper_dir=%s metal=%s pair=%s/%s",
            helper_path,
            metal_symbol,
            base_currency,
            quote_currency,
        )
        try:
            completed = subprocess.run(
                [npm_bin, "run", "--silent", "rate:once"],
                cwd=helper_path,
                env=env,
                text=True,
                capture_output=True,
                timeout=self.timeout_seconds,
                check=False,
            )
        except FileNotFoundError as exc:
            raise RateDataError(
                f"Unable to run {self.npm_bin!r}. Install Node.js/npm and run npm install in {helper_path}."
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise RateDataError(f"Node mppx rate helper timed out after {self.timeout_seconds} seconds") from exc

        if completed.stderr:
            logger.info("Node mppx helper stderr=%s", redact_helper_output(completed.stderr.strip()))

        if completed.returncode != 0:
            safe_stdout = redact_helper_output(completed.stdout.strip())
            safe_stderr = redact_helper_output(completed.stderr.strip())
            raise RateDataError(
                "Node mppx rate helper failed "
                f"exit_code={completed.returncode} stdout={safe_stdout!r} stderr={safe_stderr!r}"
            )

        try:
            payload = json.loads(completed.stdout)
        except json.JSONDecodeError as exc:
            safe_stdout = redact_helper_output(completed.stdout.strip())
            raise RateDataError(f"Node mppx rate helper did not return clean JSON stdout={safe_stdout!r}") from exc

        if not isinstance(payload, dict) or payload.get("ok") is not True:
            safe_payload = redact_helper_output(json.dumps(payload, ensure_ascii=False, default=str))
            raise RateDataError(f"Node mppx rate helper returned an error payload={safe_payload}")

        run_payload = payload.get("run")
        if not isinstance(run_payload, dict):
            raise RateDataError("Node mppx rate helper response did not include run data")

        return RateSnapshot(
            gold=parse_gold_quote(run_payload.get("gold"), symbol=metal_symbol),
            usd_vnd=parse_currency_quote(run_payload.get("currency"), label=f"{base_currency}/{quote_currency}"),
        )
