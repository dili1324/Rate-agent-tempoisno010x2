import { ACCESS_KEY_DAILY_LIMIT_USDC, ACCESS_KEY_EXPIRY_DAYS } from './config.js'
import { printJson } from './log.js'
import { authorizeAccessKey, createProvider } from './wallet.js'

async function main(): Promise<void> {
  const provider = createProvider()
  const authorization = await authorizeAccessKey(provider)

  printJson({
    ok: true,
    mode: 'mppx-access-key',
    ...authorization,
    dailyLimitUsdc: ACCESS_KEY_DAILY_LIMIT_USDC,
    expiryDays: ACCESS_KEY_EXPIRY_DAYS,
    nextStep: 'Run npm run rate:twice. The helper uses the access key saved by the accounts CLI provider.',
  })
}

main().catch((error: unknown) => {
  const message = error instanceof Error ? error.message : String(error)
  printJson({ ok: false, error: message })
  process.exitCode = 1
})
