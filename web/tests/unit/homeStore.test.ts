import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { api } from '../../src/shared/http'
import { useHomeStore } from '../../src/stores/home'
import { usePortfolioStore } from '../../src/stores/portfolio'
import { useRefreshCoordinatorStore } from '../../src/stores/refreshCoordinator'
import { useSessionCoordinatorStore } from '../../src/stores/sessionCoordinator'

vi.mock('../../src/shared/http', () => ({
  api: {
    get: vi.fn(),
    post: vi.fn(),
  },
}))

describe('home store', () => {
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
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('初始化首页时会统一加载首页读状态并启动刷新编排', async () => {
    const apiGet = vi.mocked(api.get)
    const apiPost = vi.mocked(api.post)
    const portfolioStore = usePortfolioStore()
    const refreshCoordinatorStore = useRefreshCoordinatorStore()
    const sessionCoordinatorStore = useSessionCoordinatorStore()

    portfolioStore.portfolio = [
      {
        code: 'sh600000',
        name: '浦发银行',
        qty: 10,
        price: 10,
        current_price: 12,
        yclose: 11,
        cost: 100,
        raw_cost_total: 100,
        value: 120,
        total_pnl: 20,
        day_pnl_aggregate: 10,
        day_pnl_rate_aggregate: 0.1,
        market: 'a',
        category_type: 'a',
        curr: 'CNY',
      },
    ]

    refreshCoordinatorStore.refreshStaticOnly = vi.fn().mockResolvedValue({
      flow: 'web.store.refreshStaticOnly',
      ok: true,
      stage: 'done',
      startedAt: '2026-03-16T10:00:00.000Z',
      endedAt: '2026-03-16T10:00:01.000Z',
      durationMs: 1000,
    }) as any
    refreshCoordinatorStore.refreshQuotesOnly = vi.fn().mockResolvedValue({
      flow: 'web.store.refreshQuotesOnly',
      ok: true,
      stage: 'done',
      startedAt: '2026-03-16T10:00:01.000Z',
      endedAt: '2026-03-16T10:00:02.000Z',
      durationMs: 1000,
    }) as any
    refreshCoordinatorStore.startAutoRefresh = vi.fn()
    refreshCoordinatorStore.stopAutoRefresh = vi.fn()
    sessionCoordinatorStore.bootstrap = vi.fn().mockResolvedValue({
      flow: 'web.auth.bootstrap',
      ok: true,
      stage: 'skip:no-token',
      startedAt: '2026-03-16T10:00:00.000Z',
      endedAt: '2026-03-16T10:00:00.100Z',
      durationMs: 100,
    }) as any

    apiGet.mockImplementation(async (path: string) => {
      if (path === '/api/market/indices') {
        return [{ name: '上证指数', value: 3210.12, change_pct: 0.56 }]
      }
      throw new Error(`Unexpected GET ${path}`)
    })
    apiPost.mockImplementation(async (path: string, body?: unknown) => {
      if (path === '/api/sync/bootstrap') {
        expect(body).toMatchObject({
          include: ['cash_assets', 'other_assets', 'liabilities', 'history'],
          client_versions: {},
        })
        return {
          data: {
            cash_assets: [{ id: 1, name: '招行活期', amount: 1000, curr: 'CNY' }],
            other_assets: [{ id: 2, name: '黄金', amount: 200, curr: 'CNY' }],
            liabilities: [{ id: 3, name: '信用卡', amount: 300, curr: 'CNY' }],
            history: [{ date: '2026-03-15', total_asset: 12345, day_pnl: 80 }],
          },
        }
      }
      if (path === '/api/asset/trends') {
        return {
          items: {
            sh600000: {
              code: 'sh600000',
              points: [
                { date: '2026-03-14', value: 10 },
                { date: '2026-03-15', value: 12 },
              ],
            },
          },
        }
      }
      throw new Error(`Unexpected POST ${path}`)
    })

    const homeStore = useHomeStore()
    await homeStore.initializePage()

    expect(sessionCoordinatorStore.bootstrap).toHaveBeenCalledTimes(1)
    expect(refreshCoordinatorStore.refreshStaticOnly).toHaveBeenCalledTimes(1)
    expect(refreshCoordinatorStore.refreshQuotesOnly).toHaveBeenCalledTimes(1)
    expect(refreshCoordinatorStore.startAutoRefresh).toHaveBeenCalledTimes(1)
    expect(homeStore.cashAssets).toHaveLength(1)
    expect(homeStore.otherAssets).toHaveLength(1)
    expect(homeStore.liabilities).toHaveLength(1)
    expect(homeStore.marketIndices).toHaveLength(1)
    expect(homeStore.historyPoints[0]?.total_asset).toBe(12345)
    expect(homeStore.trendMap.sh600000?.points).toHaveLength(2)

    homeStore.disposePage()
    expect(refreshCoordinatorStore.stopAutoRefresh).toHaveBeenCalledTimes(1)
  })
})
