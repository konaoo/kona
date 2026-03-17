import { clearAuth, persistAuth, readAccessToken, readRefreshToken } from './auth'
import {
  buildRequestTraceHeaders,
  getResponseRequestId,
  newRequestId,
} from './requestTrace'
import { resolveErrorMessage } from './errorText'

export type ApiError = Error & { status?: number; payload?: unknown; requestId?: string }
let refreshInflight: Promise<boolean> | null = null

async function parseJson(resp: Response): Promise<unknown> {
  const text = await resp.text()
  if (!text) return {}
  try {
    return JSON.parse(text)
  } catch {
    return { raw: text }
  }
}

async function refreshTokenIfNeeded(requestId: string): Promise<boolean> {
  if (refreshInflight) {
    return refreshInflight
  }
  refreshInflight = (async () => {
    const refreshToken = readRefreshToken()
    if (!refreshToken) return false

    const resp = await fetch('/api/auth/refresh', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...buildRequestTraceHeaders(requestId),
      },
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
  })()
  try {
    return await refreshInflight
  } finally {
    refreshInflight = null
  }
}

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
  auth = true,
  retry = true,
  requestId = newRequestId(),
): Promise<T> {
  const headers = new Headers(init.headers || {})
  headers.set('X-Request-Id', requestId)
  if (!headers.has('Content-Type') && init.body) {
    headers.set('Content-Type', 'application/json')
  }
  if (auth) {
    const token = readAccessToken()
    if (token) {
      headers.set('Authorization', `Bearer ${token}`)
    }
  }

  let resp: Response
  try {
    resp = await fetch(path, { ...init, headers })
  } catch (error) {
    const err = new Error(resolveErrorMessage(error, '网络连接失败，请检查网络后重试')) as ApiError
    err.requestId = requestId
    throw err
  }
  const responseRequestId = getResponseRequestId(resp, requestId)
  if (resp.status === 401 && auth && retry) {
    const ok = await refreshTokenIfNeeded(requestId)
    if (ok) {
      return apiRequest<T>(path, init, auth, false, requestId)
    }
  }

  const payload = await parseJson(resp)
  if (!resp.ok) {
    const err = new Error(
      resolveErrorMessage(
        {
          status: resp.status,
          payload,
        },
        `请求失败（${resp.status}）`,
      ),
    ) as ApiError
    err.status = resp.status
    err.payload = payload
    err.requestId = responseRequestId
    throw err
  }
  return payload as T
}

function withRequestId(body: unknown, requestId: string): unknown {
  if (!body || Array.isArray(body) || typeof body !== 'object') return body
  const payload = body as Record<string, unknown>
  if (typeof payload.request_id === 'string' && payload.request_id.trim()) {
    return body
  }
  return {
    ...payload,
    request_id: requestId,
  }
}

export const api = {
  get: <T>(path: string, auth = true) => apiRequest<T>(path, { method: 'GET' }, auth),
  post: <T>(path: string, body?: unknown, auth = true) => {
    const requestId = newRequestId()
    return apiRequest<T>(
      path,
      {
        method: 'POST',
        headers: buildRequestTraceHeaders(requestId),
        body: body ? JSON.stringify(withRequestId(body, requestId)) : undefined,
      },
      auth,
      true,
      requestId,
    )
  },
}
