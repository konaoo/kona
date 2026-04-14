import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/shared/http'
import { apiRequest } from '@/shared/http'

export interface Ledger {
  id: number
  name: string
  description?: string
  sort_order: number
  is_default: boolean | number
  pending?: boolean
}

export const useLedgerScopeStore = defineStore('ledgerScope', () => {
  const ledgers = ref<Ledger[]>([])
  const currentLedgerId = ref<number | null>(null)
  const loading = ref(false)

  const currentLedger = computed(() => {
    if (currentLedgerId.value == null) return ledgers.value[0] ?? null
    return ledgers.value.find(l => l.id === currentLedgerId.value) ?? ledgers.value[0] ?? null
  })

  const currentLedgerName = computed(() => currentLedger.value?.name ?? '默认账本')

  function isDefault(ledger: Ledger): boolean {
    return ledger.is_default === true || ledger.is_default === 1
  }

  function pickLedgerSelection(list: Ledger[], preferredId?: number | null): number | null {
    if (list.length === 0) return null
    if (preferredId != null && list.some(l => l.id === preferredId)) return preferredId
    const def = list.find(l => isDefault(l)) ?? list[0]
    return def?.id ?? null
  }

  function setCurrentLedgerId(ledgerId: number | null) {
    currentLedgerId.value = ledgerId == null ? null : Number(ledgerId)
  }

  async function loadLedgers() {
    loading.value = true
    try {
      const data = await api.get<Ledger[]>('/api/portfolio/ledgers', true)
      ledgers.value = Array.isArray(data) ? data : []
      currentLedgerId.value = pickLedgerSelection(ledgers.value, currentLedgerId.value)
    } catch (e) {
      console.error('Failed to load ledgers:', e)
    } finally {
      loading.value = false
    }
  }

  function switchLedger(ledgerId: number) {
    if (currentLedgerId.value === ledgerId) return
    currentLedgerId.value = ledgerId
  }

  async function createLedger(name: string, description = ''): Promise<{ ok: boolean; message?: string; ledgerId?: number }> {
    const cleanName = name.trim()
    if (!cleanName) return { ok: false, message: '账本名称不能为空' }

    try {
      const result = await api.post<{ ledger_id?: number }>('/api/portfolio/ledgers', {
        name: cleanName,
        description: description.trim(),
      })
      const ledgerId = result?.ledger_id ? Number(result.ledger_id) : undefined
      await loadLedgers()
      return { ok: true, ledgerId }
    } catch (e: any) {
      return { ok: false, message: e?.message || '创建失败' }
    }
  }

  async function updateLedger(id: number, name: string, description = ''): Promise<{ ok: boolean; message?: string }> {
    try {
      await apiRequest(`/api/portfolio/ledgers/${id}`, {
        method: 'PUT',
        body: JSON.stringify({ name: name.trim(), description: description.trim() }),
      })
      await loadLedgers()
      return { ok: true }
    } catch (e: any) {
      return { ok: false, message: e?.message || '更新失败' }
    }
  }

  async function deleteLedger(id: number): Promise<{ ok: boolean; message?: string }> {
    const removedCurrent = currentLedgerId.value === id
    try {
      await apiRequest(`/api/portfolio/ledgers/${id}`, { method: 'DELETE' })
      await loadLedgers()
      if (removedCurrent) {
        currentLedgerId.value = pickLedgerSelection(ledgers.value)
      }
      return { ok: true }
    } catch (e: any) {
      return { ok: false, message: e?.message || '删除失败，账本下可能还有持仓' }
    }
  }

  async function reorderLedgers(ledgerIds: number[]): Promise<{ ok: boolean; message?: string }> {
    try {
      await apiRequest('/api/portfolio/ledgers/reorder', {
        method: 'PUT',
        body: JSON.stringify({ ledger_ids: ledgerIds }),
      })
      await loadLedgers()
      return { ok: true }
    } catch (e: any) {
      return { ok: false, message: e?.message || '排序失败' }
    }
  }

  return {
    ledgers,
    currentLedgerId,
    currentLedger,
    currentLedgerName,
    loading,
    isDefault,
    setCurrentLedgerId,
    loadLedgers,
    switchLedger,
    createLedger,
    updateLedger,
    deleteLedger,
    reorderLedgers,
  }
})
