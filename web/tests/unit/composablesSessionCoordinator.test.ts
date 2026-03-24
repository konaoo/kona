import { beforeEach, describe, expect, it } from 'vitest'
import { createPinia, setActivePinia } from 'pinia'
import { useKonaStore } from '../../src/stores/composables'
import { useSessionCoordinatorStore } from '../../src/stores/sessionCoordinator'

describe('composables session coordinator bridge', () => {
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

  it('keeps auth bootstrap and login actions on the unified kona store entry', async () => {
    const store = useKonaStore()
    const sessionCoordinatorStore = useSessionCoordinatorStore()

    expect(store.lastBootstrapResult.value).toBeNull()

    const result = await store.bootstrap()

    expect(result.stage).toBe('skip:no-token')
    expect(store.lastBootstrapResult.value?.stage).toBe('skip:no-token')
    expect(sessionCoordinatorStore.bootstrapped).toBe(true)
    expect(typeof store.login).toBe('function')
    expect(typeof store.register).toBe('function')
    expect(typeof store.logout).toBe('function')
  })
})
