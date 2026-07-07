from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from rate_agent.mppx_rate_client import MppxRateClient
from rate_agent.rate_client import RateDataError


def test_mppx_rate_client_parses_helper_json(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    payload = {
        "ok": True,
        "run": {
            "gold": {"data": {"data": [{"date": "2026-07-07", "value": "2035.42"}]}},
            "currency": {"Realtime Currency Exchange Rate": {"5. Exchange Rate": "25234.1234"}},
        },
    }
    calls: list[dict[str, Any]] = []

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append({"args": args, "kwargs": kwargs})
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=json.dumps(payload),
            stderr="[mppx-helper] ok",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    client = MppxRateClient(helper_dir=str(tmp_path), timeout_seconds=10)
    snapshot = client.get_snapshot(metal_symbol="XAU", base_currency="USD", quote_currency="VND")

    assert snapshot.gold.value == "2035.42"
    assert snapshot.usd_vnd.value == "25234.1234"
    assert calls[0]["args"][0][1:] == ["run", "--silent", "rate:once"]
    assert Path(calls[0]["args"][0][0]).name == "npm"
    assert calls[0]["kwargs"]["cwd"] == tmp_path
    assert calls[0]["kwargs"]["env"]["METAL_SYMBOL"] == "XAU"


def test_mppx_rate_client_rejects_dirty_stdout(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout="npm noise\n{}",
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    client = MppxRateClient(helper_dir=str(tmp_path), timeout_seconds=10)

    with pytest.raises(RateDataError):
        client.get_snapshot(metal_symbol="XAU", base_currency="USD", quote_currency="VND")
