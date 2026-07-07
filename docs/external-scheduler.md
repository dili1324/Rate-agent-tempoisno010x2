# External Scheduler

Rate Agent does not use GitHub Actions `schedule`. Use cron-job.org to call the workflow dispatch API daily at 07:30 GMT+7.

## Request

```text
POST https://api.github.com/repos/dili1324/Rate-agent-tempoisno010x2/actions/workflows/rate-agent.yml/dispatches
```

Headers:

```text
Accept: application/vnd.github+json
Authorization: Bearer <GITHUB_TOKEN>
X-GitHub-Api-Version: 2022-11-28
Content-Type: application/json
```

Body:

```json
{"ref":"main"}
```

07:30 GMT+7 is 00:30 UTC.

## Workflow

The dispatched workflow is `.github/workflows/rate-agent.yml` with name `Rate Agent`.

The workflow restores the Tempo accounts CLI store from GitHub Secrets, installs Python and Node dependencies, checks wallet readiness, and runs:

```bash
python -m rate_agent
```

## GitHub Secrets

- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `TEMPO_ACCOUNTS_CLI_STORE_B64_PART1`
- `TEMPO_ACCOUNTS_CLI_STORE_B64_PART2`

## GitHub Variables

- `RATE_SOURCE`
- `RATE_PAYMENT_MODE`
- `BASE_CURRENCY`
- `QUOTE_CURRENCY`
- `METAL_SYMBOL`
- `TIMEZONE`
- `MPP_MAX_SPEND_USD`
- `MPPX_COMMAND_TIMEOUT_SECONDS`
