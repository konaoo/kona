import { describe, expect, it } from 'vitest'
import type { PositionRow } from '../../src/stores/types'
import {
  buildMarketSummaries,
  buildPortfolioSummary,
  resolvePositionDayPnlCny,
  resolvePositionTotalPnlCny,
  resolvePositionValueCny
} from '../../src/stores/portfolioMetrics'

function makeRow(overrides: Partial<PositionRow> = {}): PositionRow {
  return {
    code: 'sh600000',
    market: 'a',
    category: 'a',
    qty: 10,
    costPrice: 10,
    rawCostPrice: 10,
    displayCostPrice: 10,
    cost: 100,
    rawCostTotal: 100,
    currentPrice: 12,
    yclose: 11,
    value: 120,
    totalPnl: 20,
    dayPnl: 10,
    dayPnlRate: 0,
    dayPnlDisplay: 10,
    dayPnlRateDisplay: 0,
    dayPnlAggregate: 10,
    dayPnlRateAggregate: 0,
    totalPnlRate: 0,
    session: 'closed',
    marketOpen: false,
    marketTradingDay: false,
    marketStatusReason: '',
    usExtendedActive: false,
    navUpdatePending: false,
    quoteReady: true,
    quotePending: false,
    dayPnlDisplayEnabled: true,
    dayPnlAggregateEnabled: true,
    ...overrides
  }
}

describe('portfolioMetrics', () => {
  it('优先使用后端给出的 CNY 指标', () => {
    const row = makeRow({
      valueCny: 1200,
      totalPnlCny: 300,
      dayPnlAggregateCny: 80,
      costCny: 900,
      rateToCny: 7.2,
      value: 999,
      totalPnl: 999,
      dayPnlAggregate: 999,
      cost: 999
    })

    expect(resolvePositionValueCny(row)).toBe(1200)
    expect(resolvePositionTotalPnlCny(row)).toBe(300)
    expect(resolvePositionDayPnlCny(row)).toBe(80)
  })

  it('缺少 CNY 指标时回退到后端行指标乘汇率', () => {
    const row = makeRow({
      market: 'us',
      category: 'us',
      value: 100,
      totalPnl: 20,
      dayPnlAggregate: 5,
      cost: 80,
      rateToCny: 7.2
    })

    expect(resolvePositionValueCny(row)).toBe(720)
    expect(resolvePositionTotalPnlCny(row)).toBe(144)
    expect(resolvePositionDayPnlCny(row)).toBe(36)
  })

  it('统一汇总口径和市场拆分口径', () => {
    const rows = [
      makeRow({
        market: 'a',
        category: 'a',
        valueCny: 1000,
        costCny: 900,
        totalPnlCny: 120,
        dayPnlAggregateCny: 30
      }),
      makeRow({
        code: 'gb_aapl',
        market: 'us',
        category: 'us',
        value: 100,
        cost: 80,
        totalPnl: 20,
        dayPnlAggregate: 5,
        rateToCny: 7.2
      })
    ]

    const summary = buildPortfolioSummary(rows)
    expect(summary.totalValue).toBe(1720)
    expect(summary.totalCostAbs).toBe(1476)
    expect(summary.todayPnl).toBe(66)
    expect(summary.totalPnl).toBe(264)

    const marketSummaries = buildMarketSummaries(rows)
    const a = marketSummaries.find(item => item.market === 'a')
    const us = marketSummaries.find(item => item.market === 'us')
    expect(a?.mv).toBe(1000)
    expect(us?.mv).toBe(720)
    expect(us?.totalPnl).toBe(144)
  })
})
