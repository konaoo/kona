import { clearAuth, persistAuth, readAccessToken, readRefreshToken } from './auth'

export type ApiError = Error & { status?: number; payload?: unknown }

async function parseJson(resp: Response): Promise<unknown> {
  const text = await resp.text()
  if (!text) return {}
  try {
    return JSON.parse(text)
  } catch {
    return { raw: text }
  }
}

async function refreshTokenIfNeeded(): Promise<boolean> {
  const refreshToken = readRefreshToken()
  if (!refreshToken) return false

  const resp = await fetch('/api/auth/refresh', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token: refreshToken }),
  })

  if (!resp.ok) {
    clearAuth()
    return false
  }

  const payload = (await parseJson(resp)) as Record<string, unknown>
  const nextAccess = String(payload.access_token || '')
  const nextRefresh = String(payload.refresh_token || '')
  if (!nextAccess || !nextRefresh) {
    clearAuth()
    return false
  }
  persistAuth(nextAccess, nextRefresh, payload.user)
  return true
}

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
  auth = true,
  retry = true,
): Promise<T> {
  const headers = new Headers(init.headers || {})
  if (!headers.has('Content-Type') && init.body) {
    headers.set('Content-Type', 'application/json')
  }
  if (auth) {
    const token = readAccessToken()
    if (token) {
      headers.set('Authorization', `Bearer ${token}`)
    }
  }

  const resp = await fetch(path, { ...init, headers })
  if (resp.status === 401 && auth && retry) {
    const ok = await refreshTokenIfNeeded()
    if (ok) {
      return apiRequest<T>(path, init, auth, false)
    }
  }

  const payload = await parseJson(resp)
  if (!resp.ok) {
    const err = new Error(
      String((payload as Record<string, unknown>)?.error || `Request failed: ${resp.status}`),
    ) as ApiError
    err.status = resp.status
    err.payload = payload
    throw err
  }
  return payload as T
}

export const api = {
  get: <T>(path: string, auth = true) => apiRequest<T>(path, { method: 'GET' }, auth),
  post: <T>(path: string, body?: unknown, auth = true) =>
    apiRequest<T>(
      path,
      {
        method: 'POST',
        body: body ? JSON.stringify(body) : undefined,
      },
      auth,
    ),
}
