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
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-04-15T10:30:00+08:00'))

    const portfolioStore = usePortfolioStore()
    const quoteStore = useQuoteStore()
    const marketStore = useMarketStore()

    marketStore.marketStatus = {
      a: { open: false, trading_day: false, reason: 'holiday_or_weekend' },
      hk: { open: false, trading_day: true, reason: 'off_hours' },
      us: { open: false, trading_day: false, reason: 'holiday_or_weekend' },
      fund: { open: false, trading_day: false, reason: 'holiday_or_weekend' },
    }

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

  it('缺少 current_price 时，港股现价仍可回退到 quote_price 或 value/qty', () => {
    const portfolioStore = usePortfolioStore()

    portfolioStore.portfolio = [
      {
        code: '00175.HK',
        name: '吉利汽车',
        qty: 1000,
        price: 15,
        display_cost_price: 15,
        cost: 15000,
        raw_cost_total: 15000,
        quote_price: 23.92,
        yclose: 24.1,
        value: 23920,
        market: 'hk',
        category_type: 'hk',
        asset_type: 'hk',
        curr: 'HKD',
      },
      {
        code: '00700.HK',
        name: '腾讯控股',
        qty: 100,
        price: 500,
        display_cost_price: 500,
        cost: 50000,
        raw_cost_total: 50000,
        yclose: 522.5,
        value: 52000,
        market: 'hk',
        category_type: 'hk',
        asset_type: 'hk',
        curr: 'HKD',
      },
    ]

    const geely = portfolioStore.rows.find(item => item.code === '00175.HK')
    const tencent = portfolioStore.rows.find(item => item.code === '00700.HK')

    expect(geely?.currentPrice).toBeCloseTo(23.92)
    expect(tencent?.currentPrice).toBeCloseTo(520)
  })

  it('有实时行情时累计盈亏也要保留 adjustment_total', () => {
    const portfolioStore = usePortfolioStore()
    const quoteStore = useQuoteStore()

    portfolioStore.portfolio = [
      {
        code: 'ft_LU1116320737',
        name: '汇丰贝莱德基金',
        qty: 3043.93,
        price: 8.9881863249,
        display_cost_price: 8.9881863249,
        cost: 27359.72,
        raw_cost_total: 27359.72,
        current_price: 9.52,
        yclose: 9.5,
        value: 28978.93,
        adjustment_total: 2231.28,
        total_pnl: 3850.49,
        total_pnl_rate: 14.07,
        market: 'fund',
        category_type: 'fund',
        asset_type: 'fund',
        curr: 'USD',
        rate_to_cny: 7.23,
        value_cny: 209017.66,
        cost_cny: 197810.78,
        total_pnl_cny: 27839.02,
      },
    ]

    quoteStore.quotes = {
      ft_LU1116320737: {
        price: 9.52,
        yclose: 9.5,
      },
    }

    const row = portfolioStore.rows[0]
    expect(row?.totalPnl).toBeCloseTo(3849.7736, 4)
    expect(row?.totalPnlCny).toBeCloseTo(27833.8631, 4)

    const summary = portfolioStore.summary
    expect(summary.totalPnl).toBeCloseTo(27833.8631, 4)
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

  it('美股休市但仍是交易日时，不应继续显示今日盈亏', () => {
    const portfolioStore = usePortfolioStore()
    const quoteStore = useQuoteStore()
    const marketStore = useMarketStore()

    marketStore.marketStatus = {
      a: { open: true, trading_day: true, reason: 'open_session' },
      hk: { open: true, trading_day: true, reason: 'open_session' },
      us: { open: false, trading_day: true, reason: 'off_hours' },
      fund: { open: true, trading_day: true, reason: 'open_session' },
    }

    portfolioStore.portfolio = [
      {
        code: 'gb_goog',
        name: '谷歌',
        qty: 10,
        price: 313,
        display_cost_price: 313,
        cost: 3130,
        raw_cost_total: 3130,
        current_price: 339.4,
        yclose: 332.77,
        value: 3394,
        total_pnl: 264,
        total_pnl_rate: 8.43,
        day_pnl_aggregate: 66.3,
        day_pnl_base_aggregate: 3327.7,
        day_pnl_rate_aggregate: 1.99,
        day_pnl_aggregate_cny: 478.89,
        day_pnl_base_aggregate_cny: 24057.57,
        market: 'us',
        category_type: 'us',
        asset_type: 'us',
        curr: 'USD',
        rate_to_cny: 7.223,
      },
    ]

    quoteStore.quotes = {
      gb_goog: {
        price: 339.4,
        yclose: 332.77,
        session: 'closed',
        effective_session: 'closed',
        extended_active: false,
      },
    }

    const row = portfolioStore.rows[0]
    expect(row?.dayPnlAggregateEnabled).toBe(false)
    expect(row?.dayPnlAggregate).toBe(0)
    expect(row?.dayPnlAggregateCny).toBe(0)
    expect(row?.dayPnlDisplayEnabled).toBe(false)

    const summary = portfolioStore.summary
    expect(summary.todayPnl).toBe(0)
  })

  it('美股盘前扩展时段仍允许显示今日盈亏', () => {
    const portfolioStore = usePortfolioStore()
    const quoteStore = useQuoteStore()
    const marketStore = useMarketStore()

    marketStore.marketStatus = {
      a: { open: true, trading_day: true, reason: 'open_session' },
      hk: { open: true, trading_day: true, reason: 'open_session' },
      us: { open: false, trading_day: true, reason: 'off_hours' },
      fund: { open: true, trading_day: true, reason: 'open_session' },
    }

    portfolioStore.portfolio = [
      {
        code: 'gb_goog',
        name: '谷歌',
        qty: 10,
        price: 313,
        display_cost_price: 313,
        cost: 3130,
        raw_cost_total: 3130,
        current_price: 339.4,
        yclose: 332.77,
        value: 3394,
        total_pnl: 264,
        total_pnl_rate: 8.43,
        market: 'us',
        category_type: 'us',
        asset_type: 'us',
        curr: 'USD',
        rate_to_cny: 7.223,
      },
    ]

    quoteStore.quotes = {
      gb_goog: {
        price: 339.4,
        yclose: 332.77,
        session: 'pre',
        effective_session: 'pre',
        extended_active: true,
      },
    }

    const row = portfolioStore.rows[0]
    expect(row?.dayPnlAggregateEnabled).toBe(true)
    expect(row?.dayPnlAggregate).toBeCloseTo(66.3)
    expect(row?.dayPnlDisplayEnabled).toBe(true)
  })
})
