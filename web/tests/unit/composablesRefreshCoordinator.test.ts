import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useKonaStore } from '../../src/stores/composables'
import { useRefreshCoordinatorStore } from '../../src/stores/refreshCoordinator'

describe('composables refresh coordinator bridge', () => {
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
  })

  it('keeps refresh actions on the unified kona store entry', () => {
    const store = useKonaStore()
    const refreshCoordinatorStore = useRefreshCoordinatorStore()

    expect(store.refreshAll).toBe(refreshCoordinatorStore.refreshAll)
    expect(store.refreshAllForce).toBe(refreshCoordinatorStore.refreshAllForce)
    expect(store.refreshStaticOnly).toBe(refreshCoordinatorStore.refreshStaticOnly)
    expect(store.refreshQuotesOnly).toBe(refreshCoordinatorStore.refreshQuotesOnly)
    expect(store.startAutoRefresh).toBe(refreshCoordinatorStore.startAutoRefresh)
    expect(store.stopAutoRefresh).toBe(refreshCoordinatorStore.stopAutoRefresh)
    expect(store.lastRefreshResult.value).toBeNull()

    refreshCoordinatorStore.lastRefreshResult = {
      flow: 'web.store.refreshAll',
      ok: true,
      stage: 'done',
      startedAt: '2026-03-16T00:00:00.000Z',
      endedAt: '2026-03-16T00:00:01.000Z',
      durationMs: 1000,
    }

    expect(store.lastRefreshResult.value?.flow).toBe('web.store.refreshAll')
  })
})
