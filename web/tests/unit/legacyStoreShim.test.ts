import { describe, expect, it } from 'vitest'
import { useKonaStore as useLegacyKonaStore } from '../../src/shared/store'
import { useKonaStore } from '../../src/stores/composables'

describe('legacy shared store shim', () => {
  it('forwards the old import path to the new composables entry', () => {
    expect(useLegacyKonaStore).toBe(useKonaStore)
  })
})
