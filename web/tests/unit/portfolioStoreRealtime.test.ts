import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { usePortfolioStore } from '../../src/stores/portfolio'
import { useQuoteStore } from '../../src/stores/quote'
import { useMarketStore } from '../../src/stores/market'

describe('portfolio store realtime quotes', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  afterEach(() => {
    vi.useRealTimers()
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

  it('场外基金待净值更新时不应用实时行情覆盖今日盈亏', () => {
    const portfolioStore = usePortfolioStore()
    const quoteStore = useQuoteStore()

    portfolioStore.portfolio = [
      {
        code: 'f_110018',
        name: '易方达增强回报B',
        qty: 1000,
        price: 1.12,
        display_cost_price: 1.12,
        cost: 1120,
        raw_cost_total: 1120,
        current_price: 1.12,
        yclose: 1.12,
        value: 1120,
        total_pnl: 0,
        total_pnl_rate: 0,
        day_pnl_aggregate: 0,
        day_pnl_base_aggregate: 0,
        day_pnl_rate_aggregate: 0,
        day_pnl_aggregate_cny: 0,
        day_pnl_base_aggregate_cny: 0,
        market: 'fund',
        category_type: 'fund',
        asset_type: 'fund',
        curr: 'CNY',
        rate_to_cny: 1,
        value_cny: 1120,
        cost_cny: 1120,
        nav_update_pending: true,
        day_pnl_display_enabled: false,
        day_pnl_aggregate_enabled: false,
      },
    ]

    quoteStore.quotes = {
      f_110018: {
        price: 1.09,
        yclose: 1.12,
      },
    }

    const row = portfolioStore.rows[0]
    expect(row?.currentPrice).toBe(1.09)
    expect(row?.dayPnlAggregate).toBe(0)
    expect(row?.dayPnlAggregateCny).toBe(0)
    expect(row?.dayPnlAggregateEnabled).toBe(false)

    const summary = portfolioStore.summary
    expect(summary.todayPnl).toBe(0)
  })

  it('交易日盘前的场内基金不应把昨收涨跌提前算进今天', () => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-03-24T09:15:00+08:00'))

    const portfolioStore = usePortfolioStore()
    const quoteStore = useQuoteStore()
    const marketStore = useMarketStore()

    marketStore.marketStatus = {
      a: { open: false, trading_day: true, reason: 'off_hours' },
      hk: { open: false, trading_day: true, reason: 'off_hours' },
      us: { open: false, trading_day: false, reason: 'holiday_or_weekend' },
      fund: { open: false, trading_day: true, reason: 'off_hours' },
    }

    portfolioStore.portfolio = [
      {
        code: 'sh511360',
        name: '短融ETF',
        qty: 1000,
        price: 100,
        display_cost_price: 100,
        cost: 100000,
        raw_cost_total: 100000,
        current_price: 101,
        yclose: 100,
        value: 101000,
        total_pnl: 1000,
        total_pnl_rate: 1,
        day_pnl_aggregate: 1000,
        day_pnl_base_aggregate: 100000,
        day_pnl_rate_aggregate: 1,
        day_pnl_aggregate_cny: 1000,
        day_pnl_base_aggregate_cny: 100000,
        market: 'a',
        category_type: 'fund',
        asset_type: 'a',
        curr: 'CNY',
        rate_to_cny: 1,
        value_cny: 101000,
        cost_cny: 100000,
        day_pnl_display_enabled: true,
        day_pnl_aggregate_enabled: true,
      },
    ]

    quoteStore.quotes = {
      sh511360: {
        price: 101.5,
        yclose: 100.5,
      },
    }

    const row = portfolioStore.rows[0]
    expect(row?.category).toBe('fund')
    expect(row?.dayPnlAggregate).toBe(0)
    expect(row?.dayPnlAggregateCny).toBe(0)
    expect(row?.dayPnlAggregateEnabled).toBe(false)

    const summary = portfolioStore.summary
    expect(summary.todayPnl).toBe(0)
  })
})
