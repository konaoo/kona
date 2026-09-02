import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { api } from '../../src/shared/http'
import { useAnalysisStore } from '../../src/stores/analysis'

vi.mock('../../src/shared/http', () => ({
  api: {
    get: vi.fn(),
  },
}))

describe('分析页收益日历月份切换', () => {
  beforeEach(() => {
    const storage = new Map<string, string>()
    Object.defineProperty(globalThis, 'localStorage', {
      configurable: true,
      value: {
        getItem: (key: string) => storage.get(key) ?? null,
        setItem: (key: string, value: string) => storage.set(key, value),
        removeItem: (key: string) => storage.delete(key),
        clear: () => storage.clear(),
      },
    })
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-09-02T10:00:00+08:00'))
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  it('可在已有月份之间前后切换，且不会越过当前月', async () => {
    const apiGet = vi.mocked(api.get)
    apiGet.mockImplementation(async (path: string) => {
      const params = new URLSearchParams(path.split('?')[1])
      return {
        calendar: {
          period: {
            year: Number(params.get('year')),
            month: Number(params.get('month')),
          },
          selectable: {
            day: {
              years: [2026],
              months_by_year: { '2026': [7, 8, 9] },
            },
          },
        },
      }
    })

    const store = useAnalysisStore()
    store.selectableDayYears = [2026]
    store.selectableDayMonthsByYear = { '2026': [7, 8, 9] }
    store.selectedDayYear = 2026
    store.selectedDayMonth = 8

    expect(store.canGoToPreviousDayMonth).toBe(true)
    expect(store.canGoToNextDayMonth).toBe(true)

    store.moveDayMonth(-1)
    await vi.runAllTimersAsync()
    expect(store.selectedDayMonth).toBe(7)
    expect(apiGet).toHaveBeenLastCalledWith('/api/analysis/screen?type=day&year=2026&month=7')

    store.moveDayMonth(1)
    await vi.runAllTimersAsync()
    expect(store.selectedDayMonth).toBe(8)

    store.moveDayMonth(1)
    await vi.runAllTimersAsync()
    expect(store.selectedDayMonth).toBe(9)
    expect(store.canGoToNextDayMonth).toBe(false)
  })
})
