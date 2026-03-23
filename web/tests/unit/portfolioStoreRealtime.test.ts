import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { usePortfolioStore } from '../../src/stores/portfolio'
import { useQuoteStore } from '../../src/stores/quote'

describe('portfolio store realtime quotes', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('只更新 quotes 时 rows 和 summary 也会跟着实时变化', () => {
    const portfolioStore = usePortfolioStore()
    const quoteStore = useQuoteStore()

    portfolioStore.portfolio = [
      {
        code: 'hk0175',
        name: '吉利汽车',
        qty: 1000,
        price: 15,
        display_cost_price: 15,
        cost: 15000,
        raw_cost_total: 15000,
        current_price: 15.2,
        yclose: 15,
        value: 15200,
        total_pnl: 200,
        total_pnl_rate: 1.33,
        day_pnl_aggregate: 200,
        day_pnl_base_aggregate: 15000,
        day_pnl_rate_aggregate: 1.33,
        market: 'hk',
        category_type: 'hk',
        curr: 'HKD',
        rate_to_cny: 0.92,
        value_cny: 13984,
        cost_cny: 13800,
      },
    ]

    quoteStore.quotes = {
      hk0175: {
        price: 15.8,
        yclose: 15.3,
      },
    }

    const row = portfolioStore.rows[0]
    expect(row?.currentPrice).toBe(15.8)
    expect(row?.yclose).toBe(15.3)
    expect(row?.value).toBe(15800)
    expect(row?.dayPnlAggregate).toBeCloseTo(500)
    expect(row?.dayPnlAggregateCny).toBeCloseTo(460)
    expect(row?.totalPnl).toBeCloseTo(800)
    expect(row?.totalPnlCny).toBeCloseTo(736)

    const summary = portfolioStore.summary
    expect(summary.totalValue).toBeCloseTo(14536)
    expect(summary.todayPnl).toBeCloseTo(460)
    expect(summary.totalPnl).toBeCloseTo(736)
  })
})
