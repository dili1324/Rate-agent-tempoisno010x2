const sensitiveKeys = new Set([
  'accesskey',
  'access_key',
  'authcode',
  'auth_code',
  'bearertoken',
  'bearer_token',
  'privatekey',
  'private_key',
  'secret',
  'seed',
  'seedphrase',
  'seed_phrase',
  'token',
  'walletstore',
  'wallet_store',
])

function normalizeKey(key: string): string {
  return key.replace(/[-\s]/g, '_').toLowerCase()
}

function redact(value: unknown, key = ''): unknown {
  if (key && sensitiveKeys.has(normalizeKey(key))) {
    return '<redacted>'
  }
  if (typeof value === 'string') {
    return value
      .replace(/(api\.telegram\.org\/bot)[^/\s"]+/g, '$1<redacted>')
      .replace(/(code=)[^&\s"]+/g, '$1<redacted>')
      .replace(/(bearer\s+)[a-z0-9._~+/=-]+/gi, '$1<redacted>')
      .replace(
        /\b(access[-_]?key|auth[-_]?code|private[-_]?key|seed(?:[-_]?phrase)?|secret|token|wallet[-_]?store)\b(\s*[:=]\s*)("[^"]+"|'[^']+'|[^\s,}]+)/gi,
        '$1$2<redacted>',
      )
      .replace(/0x[a-fA-F0-9]{40}/g, '<redacted-address>')
  }
  if (Array.isArray(value)) {
    return value.map((item) => redact(item))
  }
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>).map(([entryKey, item]) => [
        entryKey,
        redact(item, entryKey),
      ]),
    )
  }
  return value
}

export function log(message: string, fields: Record<string, unknown> = {}): void {
  const payload = Object.keys(fields).length === 0 ? '' : ` ${JSON.stringify(redact(fields))}`
  process.stderr.write(`[mppx-helper] ${message}${payload}\n`)
}

export function printJson(value: unknown): void {
  process.stdout.write(`${JSON.stringify(redact(value), null, 2)}\n`)
}
