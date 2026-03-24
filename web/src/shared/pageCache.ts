export type CacheEnvelope<T> = {
  userId: string
  savedAt: number
  ttlMs: number
  data: T
}

function normalizeUserId(userId?: string): string {
  const value = String(userId || '').trim()
  return value || 'guest'
}

function buildKey(domain: string, key: string, userId?: string): string {
  return `web_cache:v1:u:${normalizeUserId(userId)}:${domain}:${key}`
}

export function readPageCache<T>(
  domain: string,
  key: string,
  userId: string | undefined,
  fallbackTtlMs = 0,
): T | null {
  if (typeof window === 'undefined') return null
  const cacheKey = buildKey(domain, key, userId)
  const raw = localStorage.getItem(cacheKey)
  if (!raw) return null
  try {
    const parsed = JSON.parse(raw) as CacheEnvelope<T>
    if (!parsed || typeof parsed !== 'object') {
      localStorage.removeItem(cacheKey)
      return null
    }
    const savedAt = Number(parsed.savedAt || 0)
    const ttlMs = Number(parsed.ttlMs || fallbackTtlMs || 0)
    if (!savedAt || !ttlMs) {
      return parsed.data ?? null
    }
    if (Date.now() - savedAt > ttlMs) {
      localStorage.removeItem(cacheKey)
      return null
    }
    return parsed.data ?? null
  } catch {
    localStorage.removeItem(cacheKey)
    return null
  }
}

export function writePageCache<T>(
  domain: string,
  key: string,
  userId: string | undefined,
  data: T,
  ttlMs: number,
): void {
  if (typeof window === 'undefined') return
  const cacheKey = buildKey(domain, key, userId)
  const payload: CacheEnvelope<T> = {
    userId: normalizeUserId(userId),
    savedAt: Date.now(),
    ttlMs,
    data,
  }
  try {
    localStorage.setItem(cacheKey, JSON.stringify(payload))
  } catch {
    // ignore storage errors
  }
}
