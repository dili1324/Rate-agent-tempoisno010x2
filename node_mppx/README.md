# Rate Agent MPPX Helper

This helper calls Alpha Vantage MPP endpoints through `mppx` and the `accounts/cli` provider.

## Setup

```bash
npm ci
npm run connect
```

`npm run connect` authorizes an access key and stores the provider state in the Tempo accounts CLI store. GitHub Actions restores that store from:

- `TEMPO_ACCOUNTS_CLI_STORE_B64_PART1`
- `TEMPO_ACCOUNTS_CLI_STORE_B64_PART2`

## Commands

```bash
npm run rate:once
npm run rate:twice
npm run gold
npm run currency
```

The helper uses:

- `POST /alphavantage/currency-exchange-rate`

Environment variables:

- `ALPHAVANTAGE_MPP_BASE_URL`
- `METAL_SYMBOL`
- `BASE_CURRENCY`
- `QUOTE_CURRENCY`
- `MPPX_ACCESS_KEY_DAILY_LIMIT_USDC`
- `MPPX_ACCESS_KEY_EXPIRY_DAYS`
- `MPPX_ACCESS_KEY_PERIOD_SECONDS`
