import { describe, expect, it } from 'vitest'
import type { PositionRow } from '../../src/stores/types'
import {
  buildInvestHoldingRows,
  formatLatestNavDateText,
  isFundAsset,
  resolveCurrentDayPnlSortValue
} from '../../src/stores/investHoldingRows'

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
    yclose: 10,
    value: 120,
    totalPnl: 20,
    dayPnl: 10,
    dayPnlRate: 0,
    dayPnlDisplay: 10,
    dayPnlRateDisplay: 0,
    dayPnlAggregate: 10,
    dayPnlBaseAggregate: 100,
    dayPnlRateAggregate: 10,
    totalPnlRate: 20,
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

describe('investHoldingRows', () => {
  it('按 tab 过滤，补齐展示字段，并按当前当日盈亏排序', () => {
    const rows = buildInvestHoldingRows({
      rows: [
        makeRow({ code: 'low', currentPrice: 11, yclose: 10, valueCny: 110 }),
        makeRow({ code: 'hidden', market: 'hk', category: 'hk', currentPrice: 20 }),
        makeRow({ code: 'high', currentPrice: 13, yclose: 10, valueCny: 130 })
      ],
      selectedTab: 'a',
      totalMarketValue: 260,
      trendMap: {
        high: {
          code: 'high',
          points: [
            { date: '2026-04-29', value: 10 },
            { date: '2026-04-30', value: 13 }
          ]
        }
      }
    })

    expect(rows.map(row => row.code)).toEqual(['high', 'low'])
    expect(rows[0].amount).toBe(10)
    expect(rows[0].mvCny).toBe(130)
    expect(rows[0].pct).toBe(50)
    expect(rows[0].sparkReady).toBe(true)
    expect(rows[1].spark).toBe('')
  })

  it('盘前 off_hours 的 A/H/基金排序值固定为 0，避免用旧价制造盘前涨跌排序', () => {
    const now = new Date(2026, 3, 30, 9, 0)
    const value = resolveCurrentDayPnlSortValue(
      makeRow({
        marketOpen: false,
        marketTradingDay: true,
        marketStatusReason: 'off_hours',
        currentPrice: 13,
        yclose: 10
      }),
      now
    )

    expect(value).toBe(0)
  })

  it('场外基金净值待更新时隐藏当日盈亏，并保留基金单位', () => {
    const rows = buildInvestHoldingRows({
      rows: [
        makeRow({
          code: 'f_000001',
          market: 'fund',
          category: 'fund',
          asset_type: 'fund',
          navUpdatePending: true,
          latest_nav_date: '2000-01-01',
          dayPnlAggregate: 99,
          dayPnlRateAggregate: 9
        })
      ],
      selectedTab: 'all',
      totalMarketValue: 120,
      trendMap: {}
    })

    expect(isFundAsset(rows[0])).toBe(true)
    expect(rows[0].unit).toBe('份')
    expect(rows[0].dayPnlVisible).toBe(false)
    expect(rows[0].dayPnl).toBe(0)
    expect(rows[0].dayPnlRaw).toBe(0)
  })

  it('格式化净值日期只展示月日', () => {
    expect(formatLatestNavDateText('2026-04-30T00:00:00')).toBe('04-30')
    expect(formatLatestNavDateText('invalid')).toBe('invalid')
    expect(formatLatestNavDateText(null)).toBeNull()
  })
})
