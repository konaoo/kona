const ACCESS_TOKEN_KEY = 'kona_web_access_token'
const LEGACY_REFRESH_TOKEN_KEY = 'kona_web_refresh_token'
const USER_KEY = 'kona_web_user'

export function readAccessToken(): string {
  return localStorage.getItem(ACCESS_TOKEN_KEY) || ''
}

export function readRefreshToken(): string {
  // 仅用于兼容老版本 Web，把本地 refresh token 迁到服务端 HttpOnly Cookie。
  return localStorage.getItem(LEGACY_REFRESH_TOKEN_KEY) || ''
}

export function readStoredUser<T>(): T | null {
  const raw = localStorage.getItem(USER_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as T
  } catch {
    return null
  }
}

export function persistAuth(accessToken: string, user?: unknown) {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
  localStorage.removeItem(LEGACY_REFRESH_TOKEN_KEY)
  if (user !== undefined) {
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  }
}

export function persistUser(user: unknown) {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function clearAuth() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(LEGACY_REFRESH_TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}
