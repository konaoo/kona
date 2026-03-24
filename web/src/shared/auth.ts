const ACCESS_TOKEN_KEY = 'kona_web_access_token'
const REFRESH_TOKEN_KEY = 'kona_web_refresh_token'
const USER_KEY = 'kona_web_user'

export function readAccessToken(): string {
  return localStorage.getItem(ACCESS_TOKEN_KEY) || ''
}

export function readRefreshToken(): string {
  return localStorage.getItem(REFRESH_TOKEN_KEY) || ''
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

export function persistAuth(accessToken: string, refreshToken: string, user?: unknown) {
  localStorage.setItem(ACCESS_TOKEN_KEY, accessToken)
  localStorage.setItem(REFRESH_TOKEN_KEY, refreshToken)
  if (user !== undefined) {
    localStorage.setItem(USER_KEY, JSON.stringify(user))
  }
}

export function persistUser(user: unknown) {
  localStorage.setItem(USER_KEY, JSON.stringify(user))
}

export function clearAuth() {
  localStorage.removeItem(ACCESS_TOKEN_KEY)
  localStorage.removeItem(REFRESH_TOKEN_KEY)
  localStorage.removeItem(USER_KEY)
}
