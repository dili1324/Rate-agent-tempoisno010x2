# Rate Agent

Rate Agent sends a daily Telegram message with:

- XAU/USD
- USD/VND

The primary data source is Alpha Vantage through Locus MPP:

- `POST https://alphavantage.mpp.paywithlocus.com/alphavantage/currency-exchange-rate`

GitHub Actions is manual-only. The `Rate Agent` workflow exposes `workflow_dispatch`; cron-job.org should call the GitHub Actions API every day at 07:30 GMT+7. There is no internal GitHub Actions schedule.

No `.env`, Telegram token, chat id, wallet store, private key, or seed phrase belongs in this repository.

## Runtime Flow

```text
cron-job.org -> GitHub Actions workflow_dispatch -> Python app -> Node mppx helper -> Alpha Vantage MPP -> Telegram Bot API
```

The GitHub workflow restores the Tempo accounts CLI wallet store from GitHub Secrets, matching the previous weather-agent approach. The expected wallet is:

```text
0xeDC42cA9000D7001f967b7bb51872af9f4E636c6
```

## Repository Structure

```text
.github/workflows/
  ci.yml
  rate-agent.yml
node_mppx/
src/rate_agent/
tests/
.env.example
README.md
```

## Configuration

Required GitHub Secrets:

- `TELEGRAM_BOT_TOKEN`: token for `@RateAgentBot`
- `TELEGRAM_CHAT_ID`: destination chat/channel/user id
- `TEMPO_ACCOUNTS_CLI_STORE_B64_PART1`: first base64 chunk of the Tempo accounts CLI store
- `TEMPO_ACCOUNTS_CLI_STORE_B64_PART2`: second base64 chunk, if the store is split

Recommended GitHub Variables:

- `RATE_SOURCE=alphavantage`
- `RATE_PAYMENT_MODE=mppx`
- `BASE_CURRENCY=USD`
- `QUOTE_CURRENCY=VND`
- `METAL_SYMBOL=XAU`
- `TIMEZONE=Asia/Ho_Chi_Minh`
- `MPP_MAX_SPEND_USD=0.05`
- `MPPX_COMMAND_TIMEOUT_SECONDS=120`

Local `.env.example` contains the non-secret defaults. Do not commit `.env`.

## Local Run

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements-lock.txt
.venv/bin/python -m pip install --no-build-isolation -e .
cp .env.example .env
```

Fill local Telegram and Tempo values in `.env`, then run:

```bash
set -a
source .env
set +a
.venv/bin/python -m rate_agent
```

For the mppx helper:

```bash
cd node_mppx
npm ci
npm run connect
npm run rate:once
```

## GitHub Actions

Workflow file:

```text
.github/workflows/rate-agent.yml
```

Workflow name:

```text
Rate Agent
```

Dispatch endpoint for cron-job.org:

```text
POST https://api.github.com/repos/dili1324/Rate-agent-tempoisno010x2/actions/workflows/rate-agent.yml/dispatches
```

Use body:

```json
{"ref":"main"}
```

Set cron-job.org to 07:30 GMT+7. In UTC, that is `00:30`.

## Message Format

Example Telegram message:

```text
Rate Agent - cập nhật 07:30 GMT+7 (2026-07-07 07:30 Asia/Ho_Chi_Minh)
XAU/USD: 2035.42 (USD per troy oz)
USD/VND: 25234 (VND per USD)
Nguồn: Alpha Vantage via MPP
Thời gian dữ liệu: 2026-07-07 / 2026-07-07 00:00:00
```

## Tests

```bash
python -m pytest -q
```

Tests do not spend MPP funds and do not call Telegram. They cover config, parser, formatter, mppx helper parsing, and Tempo output redaction.

## Security Checklist

- Telegram token is never logged.
- Telegram chat id is masked by `TelegramClient`.
- Tempo wallet store is restored only from GitHub Secrets.
- Tempo output redacts CLI auth codes and Telegram bot URLs.
- The workflow has no internal schedule.
- MPP spend is capped by `MPP_MAX_SPEND_USD` for Tempo CLI mode.
