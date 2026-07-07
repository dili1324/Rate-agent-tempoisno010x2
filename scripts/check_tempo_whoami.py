"""Validate `tempo wallet --format json whoami` output in CI."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

from redact_ci_log import redact_text
from rate_agent.tempo_client import _extract_json_from_output


def _print_redacted_diagnostics(stdout: str, stderr: str) -> None:
    print("stdout:")
    print(redact_text(stdout))
    print("stderr:")
    print(redact_text(stderr))


def _require_ready(parsed: Any) -> bool:
    return isinstance(parsed, dict) and parsed.get("ready") is True


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: check_tempo_whoami.py <stdout-file> <stderr-file>", file=sys.stderr)
        return 2

    stdout = Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")
    stderr = Path(sys.argv[2]).read_text(encoding="utf-8", errors="replace")
    parsed = _extract_json_from_output(stdout)

    if not isinstance(parsed, dict):
        print("Could not parse a JSON object from tempo wallet whoami stdout.")
        _print_redacted_diagnostics(stdout, stderr)
        return 1

    if not _require_ready(parsed):
        print("Tempo wallet is not ready.")
        _print_redacted_diagnostics(stdout, stderr)
        return 1

    print("Tempo wallet ready=true")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
