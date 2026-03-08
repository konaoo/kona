function guessAvatarMime(base64: string): string {
  const raw = String(base64 || '').trim()
  if (raw.startsWith('/9j/')) return 'image/jpeg'
  if (raw.startsWith('iVBORw0KGgo')) return 'image/png'
  if (raw.startsWith('R0lGOD')) return 'image/gif'
  if (raw.startsWith('UklGR')) return 'image/webp'
  return 'image/jpeg'
}

function looksLikeRawBase64(value: string): boolean {
  const raw = String(value || '').trim()
  if (!raw || raw.length < 64) return false
  if (raw.includes(' ') || raw.includes('\n') || raw.includes('\r')) return false
  return /^[A-Za-z0-9+/=]+$/.test(raw)
}

export function toAvatarSrc(value: unknown): string {
  const raw = String(value || '').trim()
  if (!raw) return ''
  if (looksLikeRawBase64(raw)) {
    return `data:${guessAvatarMime(raw)};base64,${raw}`
  }
  if (
    raw.startsWith('data:image/')
    || raw.startsWith('blob:')
    || raw.startsWith('http://')
    || raw.startsWith('https://')
    || raw.startsWith('/')
  ) {
    return raw
  }
  return raw
}
