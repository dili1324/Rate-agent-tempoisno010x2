import { Mppx, tempo } from 'mppx/client'
import {
  DEFAULT_BASE_CURRENCY,
  DEFAULT_METAL_SYMBOL,
  DEFAULT_QUOTE_CURRENCY,
  endpoint,
} from './config.js'
import { log, printJson } from './log.js'
import { createProvider } from './wallet.js'

type RateResponse = {
  gold: unknown
  currency: unknown
}

async function postJson(mppx: ReturnType<typeof Mppx.create>, path: string, payload: unknown): Promise<unknown> {
  const url = endpoint(path)
  log('request start', { url })
  const response = await mppx.fetch(url, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(payload),
  })

  const text = await response.text()
  let body: unknown
  try {
    body = text ? JSON.parse(text) : null
  } catch {
    body = text
  }

  if (!response.ok) {
    throw new Error(`MPP request failed status=${response.status} body=${JSON.stringify(body)}`)
  }

  log('request completed', { url, status: response.status })
  return body
}

async function createMppxClient(): Promise<ReturnType<typeof Mppx.create>> {
  const provider = createProvider()
  const accounts = await provider.request({ method: 'eth_accounts' })
  log('loaded wallet state', { accountCount: Array.isArray(accounts) ? accounts.length : 0 })

  if (!Array.isArray(accounts) || accounts.length === 0) {
    throw new Error('No local wallet account available. Run npm run connect first.')
  }
  const account = provider.getAccount()

  const mppx = Mppx.create({
    methods: [
      tempo({
        account,
        getClient: provider.getClient,
      }),
    ],
    paymentPreferences: { 'tempo/charge': 1, 'tempo/session': 0 },
    polyfill: false,
  })

  mppx.onChallengeReceived(({ challenge }: any) => {
    log('payment challenge received', {
      id: challenge.id,
      method: challenge.method,
      intent: challenge.intent,
    })
  })
  mppx.onCredentialCreated(({ challenge }: any) => {
    log('payment credential created', {
      id: challenge.id,
      method: challenge.method,
      intent: challenge.intent,
    })
  })
  mppx.onPaymentResponse(({ response }: any) => {
    log('payment retry response', { status: response.status })
  })
  mppx.onPaymentFailed(({ error }: any) => {
    log('payment failed', { error: error instanceof Error ? error.message : String(error) })
  })

  return mppx
}

async function goldPrice(mppx: ReturnType<typeof Mppx.create>): Promise<unknown> {
  return postJson(mppx, '/alphavantage/commodity-price', {
    commodity: 'GOLD_SILVER_SPOT',
    symbol: DEFAULT_METAL_SYMBOL,
    datatype: 'json',
  })
}

async function currencyRate(mppx: ReturnType<typeof Mppx.create>): Promise<unknown> {
  return postJson(mppx, '/alphavantage/currency-exchange-rate', {
    from_currency: DEFAULT_BASE_CURRENCY,
    to_currency: DEFAULT_QUOTE_CURRENCY,
  })
}

async function rateOnce(mppx?: ReturnType<typeof Mppx.create>): Promise<RateResponse> {
  mppx = mppx ?? (await createMppxClient())
  const goldBody = await goldPrice(mppx)
  const currencyBody = await currencyRate(mppx)
  return {
    gold: goldBody,
    currency: currencyBody,
  }
}

async function main(): Promise<void> {
  const command = process.argv[2] ?? 'once'
  const mppx = command === 'once' || command === 'twice' ? undefined : await createMppxClient()

  if (command === 'gold') {
    printJson({ ok: true, gold: await goldPrice(mppx!) })
    return
  }

  if (command === 'currency') {
    printJson({ ok: true, currency: await currencyRate(mppx!) })
    return
  }

  if (command === 'once') {
    printJson({ ok: true, run: await rateOnce() })
    return
  }

  if (command === 'twice') {
    const sharedMppx = await createMppxClient()
    log('rate twice run 1 starting')
    const first = await rateOnce(sharedMppx)
    log('rate twice run 1 completed')
    log('rate twice run 2 starting')
    const second = await rateOnce(sharedMppx)
    log('rate twice run 2 completed')
    printJson({ ok: true, runs: [first, second] })
    return
  }

  throw new Error(`Unknown command: ${command}`)
}

main().catch((error: unknown) => {
  const message = error instanceof Error ? error.message : String(error)
  printJson({ ok: false, error: message })
  process.exitCode = 1
})
