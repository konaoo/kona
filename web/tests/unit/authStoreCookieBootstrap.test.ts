import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useAuthStore } from '../../src/stores/auth'

function installLocalStorage() {
  const storage = new Map<string, string>()
  Object.defineProperty(globalThis, 'localStorage', {
    configurable: true,
    value: {
      getItem: (key: string) => storage.get(key) ?? null,
      setItem: (key: string, value: string) => {
        storage.set(key, value)
      },
      removeItem: (key: string) => {
        storage.delete(key)
      },
      clear: () => {
        storage.clear()
      },
    },
  })
  return storage
}

describe('auth store cookie bootstrap', () => {
  beforeEach(() => {
    installLocalStorage()
    Object.defineProperty(globalThis, 'fetch', {
      configurable: true,
      value: vi.fn(),
    })
    setActivePinia(createPinia())
  })

  it('本地没有 refresh token 时也能通过 cookie 续期恢复登录', async () => {
    const fetchMock = vi.mocked(globalThis.fetch)
    fetchMock
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            access_token: 'access-from-cookie',
            refresh_token: 'refresh-from-cookie',
            user: { id: 'u_cookie', username: 'cookie_user', is_admin: 0 },
          }),
          {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          },
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({
            id: 'u_cookie',
            username: 'cookie_user',
            is_admin: 0,
          }),
          {
            status: 200,
            headers: { 'Content-Type': 'application/json' },
          },
        ),
      )

    const store = useAuthStore()
    const result = await store.bootstrap()

    expect(result.stage).toBe('profile-loaded')
    expect(store.isAuthenticated).toBe(true)
    expect(store.token).toBe('access-from-cookie')
    expect(store.user?.username).toBe('cookie_user')
    expect(globalThis.localStorage.getItem('kona_web_access_token')).toBe('access-from-cookie')
    expect(globalThis.localStorage.getItem('kona_web_refresh_token')).toBeNull()

    expect(fetchMock).toHaveBeenCalledTimes(2)
    const [refreshPath, refreshInit] = fetchMock.mock.calls[0] || []
    expect(refreshPath).toBe('/api/auth/refresh')
    expect((refreshInit as RequestInit).credentials).toBe('same-origin')
    expect((refreshInit as RequestInit).body).toBe('{}')
  })
})
