import { beforeEach, describe, expect, it, vi } from 'vitest'
import { api } from '../../src/shared/http'

describe('http request trace', () => {
  beforeEach(() => {
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
    Object.defineProperty(globalThis, 'fetch', {
      configurable: true,
      value: vi.fn(),
    })
  })

  it('会为 post 自动补 request_id 并带上追踪请求头', async () => {
    const fetchMock = vi.mocked(globalThis.fetch)
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ status: 'ok' }), {
        status: 200,
        headers: { 'Content-Type': 'application/json', 'X-Request-Id': 'backend-req-1' },
      }),
    )

    await api.post('/api/portfolio/buy', { code: 'sh600000', qty: 1, price: 10 })

    expect(fetchMock).toHaveBeenCalledTimes(1)
    const [path, init] = fetchMock.mock.calls[0] || []
    expect(path).toBe('/api/portfolio/buy')
    const headers = new Headers((init as RequestInit).headers)
    const requestId = headers.get('X-Request-Id')
    expect(requestId).toMatch(/^web-/)

    const payload = JSON.parse(String((init as RequestInit).body || '{}'))
    expect(payload.code).toBe('sh600000')
    expect(payload.request_id).toBe(requestId)
  })

  it('请求失败时会把 request id 挂到错误对象上', async () => {
    const fetchMock = vi.mocked(globalThis.fetch)
    fetchMock.mockResolvedValue(
      new Response(JSON.stringify({ error: 'boom' }), {
        status: 500,
        headers: { 'Content-Type': 'application/json', 'X-Request-Id': 'backend-req-2' },
      }),
    )

    await expect(api.get('/api/history')).rejects.toMatchObject({
      status: 500,
      requestId: 'backend-req-2',
    })
  })
})
