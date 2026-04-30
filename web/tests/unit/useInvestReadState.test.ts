import { describe, expect, it, vi } from 'vitest'
import { createInvestReadState } from '../../src/pages/app/useInvestReadState'

describe('useInvestReadState', () => {
  it('刷新投资读侧状态时按顺序加载静态数据、当日实时数据、趋势，并异步触发行情刷新', async () => {
    const calls: string[] = []
    const state = createInvestReadState({
      rows: {
        value: [
          { code: 'sh600000', name: '浦发银行', category: 'a' },
          { code: '', name: '空代码', category: 'a' }
        ]
      },
      trendMap: { value: {} },
      apiPost: vi.fn(async () => {
        calls.push('trends')
        return { items: { sh600000: { code: 'sh600000', points: [] } } }
      }),
      store: {
        refreshStaticOnly: vi.fn(async () => {
          calls.push('static')
        }),
        refreshQuotesOnly: vi.fn(() => {
          calls.push('quotes')
        }),
        startAutoRefresh: vi.fn(),
        stopAutoRefresh: vi.fn()
      },
      realtimeTodayStore: {
        load: vi.fn(async () => {
          calls.push('realtime')
        })
      },
      setIntervalFn: vi.fn(),
      clearIntervalFn: vi.fn()
    })

    await state.refreshInvestReadState()

    expect(calls).toEqual(['static', 'realtime', 'trends', 'quotes'])
    expect(state.trendMap.value).toEqual({ sh600000: { code: 'sh600000', points: [] } })
  })

  it('启动和停止自动刷新时托管定时器生命周期', () => {
    const timer = 123
    const deps = {
      rows: { value: [] },
      trendMap: { value: {} },
      apiPost: vi.fn(),
      store: {
        refreshStaticOnly: vi.fn(),
        refreshQuotesOnly: vi.fn(),
        startAutoRefresh: vi.fn(),
        stopAutoRefresh: vi.fn()
      },
      realtimeTodayStore: { load: vi.fn() },
      setIntervalFn: vi.fn(() => timer),
      clearIntervalFn: vi.fn()
    }
    const state = createInvestReadState(deps)

    state.startInvestAutoRefresh()
    state.stopInvestAutoRefresh()

    expect(deps.store.startAutoRefresh).toHaveBeenCalledOnce()
    expect(deps.setIntervalFn).toHaveBeenCalledOnce()
    expect(deps.store.stopAutoRefresh).toHaveBeenCalledOnce()
    expect(deps.clearIntervalFn).toHaveBeenCalledWith(timer)
  })
})
