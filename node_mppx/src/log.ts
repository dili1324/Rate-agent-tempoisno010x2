function redact(value: unknown): unknown {
  if (typeof value === 'string') {
    return value
      .replace(/(api\.telegram\.org\/bot)[^/\s"]+/g, '$1<redacted>')
      .replace(/(code=)[^&\s"]+/g, '$1<redacted>')
      .replace(/0x[a-fA-F0-9]{40}/g, '<redacted-address>')
  }
  if (Array.isArray(value)) {
    return value.map(redact)
  }
  if (value && typeof value === 'object') {
    return Object.fromEntries(
      Object.entries(value as Record<string, unknown>).map(([key, item]) => [key, redact(item)]),
    )
  }
  return value
}

export function log(message: string, fields: Record<string, unknown> = {}): void {
  const payload = Object.keys(fields).length === 0 ? '' : ` ${JSON.stringify(redact(fields))}`
  process.stderr.write(`[mppx-helper] ${message}${payload}\n`)
}

export function printJson(value: unknown): void {
  process.stdout.write(`${JSON.stringify(value, null, 2)}\n`)
}
