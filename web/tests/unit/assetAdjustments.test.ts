import { describe, expect, it, vi } from 'vitest'
import {
  fetchAssetAdjustments,
  formatAdjustmentAmount,
  normalizeAssetAdjustmentsPayload,
} from '../../src/shared/assetAdjustments'

describe('asset adjustments helpers', () => {
  it('loads cash asset adjustment records from the backend route', async () => {
    const apiGet = vi.fn().mockResolvedValue({
      adjustments: [
        {
          id: 71,
          mode: 'add',
          delta: 25311.33,
          note: '卖出 谷歌 回款',
          balance_after: 120311.33,
          created_at: '2026-05-01 09:01:46',
        },
      ],
    })

    const records = await fetchAssetAdjustments(apiGet, 'cash', 27)

    expect(apiGet).toHaveBeenCalledWith('/api/assets/cash/27/adjustments')
    expect(records).toEqual([
      {
        id: 71,
        mode: 'add',
        delta: 25311.33,
        note: '卖出 谷歌 回款',
        balance_after: 120311.33,
        created_at: '2026-05-01 09:01:46',
      },
    ])
  })

  it('normalizes malformed adjustment payloads to an empty list', () => {
    expect(normalizeAssetAdjustmentsPayload(null)).toEqual([])
    expect(normalizeAssetAdjustmentsPayload({ adjustments: null })).toEqual([])
  })

  it('formats adjustment deltas with signs and currency symbols', () => {
    expect(formatAdjustmentAmount({ mode: 'add', delta: 25311.33 }, 'CNY')).toBe('+¥25,311.33')
    expect(formatAdjustmentAmount({ mode: 'sub', delta: 12.5 }, 'USD')).toBe('-$12.50')
  })
})
