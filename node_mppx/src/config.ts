import { isHex, type Hex } from 'viem'

export const ALPHAVANTAGE_MPP_BASE_URL =
  process.env.ALPHAVANTAGE_MPP_BASE_URL ?? 'https://alphavantage.mpp.paywithlocus.com'

export const DEFAULT_BASE_CURRENCY = process.env.BASE_CURRENCY ?? 'USD'
export const DEFAULT_QUOTE_CURRENCY = process.env.QUOTE_CURRENCY ?? 'VND'

function requireHex(value: string, name: string): Hex {
  if (!isHex(value)) {
    throw new Error(`${name} must be a 0x-prefixed hex string`)
  }
  return value
}

export const TEMPO_USDC_TOKEN = requireHex(
  process.env.TEMPO_USDC_TOKEN ?? '0x20C000000000000000000000b9537d11c60E8b50',
  'TEMPO_USDC_TOKEN',
)

export const ACCESS_KEY_DAILY_LIMIT_USDC = process.env.MPPX_ACCESS_KEY_DAILY_LIMIT_USDC ?? '1'
export const ACCESS_KEY_EXPIRY_DAYS = Number(process.env.MPPX_ACCESS_KEY_EXPIRY_DAYS ?? '7')
export const ACCESS_KEY_PERIOD_SECONDS = Number(process.env.MPPX_ACCESS_KEY_PERIOD_SECONDS ?? '86400')

export function endpoint(path: string): string {
  return `${ALPHAVANTAGE_MPP_BASE_URL}${path}`
}
