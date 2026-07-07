#!/usr/bin/env bash
set -euo pipefail

output="${1:-rate-agent-clean.zip}"

rm -f "$output"

zip -r "$output" . \
  -x ".git/*" \
  -x ".venv/*" \
  -x "node_modules/*" \
  -x "node_mppx/node_modules/*" \
  -x "__MACOSX/*" \
  -x "*/__MACOSX/*" \
  -x ".pytest_cache/*" \
  -x "*/.pytest_cache/*" \
  -x ".mypy_cache/*" \
  -x "*/.mypy_cache/*" \
  -x ".ruff_cache/*" \
  -x "*/.ruff_cache/*" \
  -x "*.egg-info/*" \
  -x "*/*.egg-info/*" \
  -x "__pycache__/*" \
  -x "*/__pycache__/*" \
  -x "*.DS_Store" \
  -x ".env" \
  -x "$output"
