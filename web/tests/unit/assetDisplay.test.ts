import { describe, expect, it } from 'vitest'
import {
  formatLatestNavDateText,
  isDateToday,
  isFundAsset,
  isStaleFund,
  readLatestNavDate,
  shouldShowFundNavMeta
} from '../../src/shared/assetDisplay'

describe('assetDisplay', () => {
  it('统一识别基金资产', () => {
    expect(isFundAsset({ category: 'fund' })).toBe(true)
    expect(isFundAsset({ asset_type: 'fund' })).toBe(true)
    expect(isFundAsset({ code: 'f_000001' })).toBe(true)
    expect(isFundAsset({ code: 'ft_LU1116320737' })).toBe(true)
    expect(isFundAsset({ market: 'us', code: 'gb_aapl' })).toBe(false)
  })

  it('只在场外基金净值待更新时展示净值日期提示', () => {
    expect(shouldShowFundNavMeta({ category: 'fund', navUpdatePending: true })).toBe(true)
    expect(shouldShowFundNavMeta({ category: 'fund', navUpdatePending: false })).toBe(false)
    expect(shouldShowFundNavMeta({ category: 'us', navUpdatePending: true })).toBe(false)
  })

  it('读取并格式化净值日期', () => {
    expect(readLatestNavDate({ latest_nav_date: '2026-04-30T00:00:00' })).toBe(
      '2026-04-30T00:00:00'
    )
    expect(readLatestNavDate({ latestNavDate: '2026-04-29' })).toBe('2026-04-29')
    expect(formatLatestNavDateText('2026-04-30T00:00:00')).toBe('04-30')
    expect(formatLatestNavDateText('unknown')).toBe('unknown')
    expect(formatLatestNavDateText(null)).toBeNull()
  })

  it('按传入日期判断是否是当天，避免测试依赖系统时钟', () => {
    const now = new Date(2026, 3, 30, 12, 0)
    expect(isDateToday('2026-04-30T00:00:00', now)).toBe(true)
    expect(isDateToday('2026-04-29T00:00:00', now)).toBe(false)
    expect(isDateToday('bad-date', now)).toBe(false)
  })

  it('只有净值待更新且净值日期不是今天的基金才 stale', () => {
    const now = new Date(2026, 3, 30, 12, 0)
    expect(
      isStaleFund({ category: 'fund', navUpdatePending: true, latest_nav_date: '2026-04-29' }, now)
    ).toBe(true)
    expect(
      isStaleFund({ category: 'fund', navUpdatePending: true, latest_nav_date: '2026-04-30' }, now)
    ).toBe(false)
    expect(isStaleFund({ category: 'fund', navUpdatePending: false }, now)).toBe(false)
    expect(isStaleFund({ category: 'us', navUpdatePending: true }, now)).toBe(false)
  })
})
