import { computed, ref } from 'vue'
import { defineStore } from 'pinia'
import { api } from '@/shared/http'
import type { RealtimeTodayPayload } from './types'
import { useLedgerScopeStore } from './ledgerScope'

export const useRealtimeTodayStore = defineStore('realtimeToday', () => {
  const ledgerScopeStore = useLedgerScopeStore()
  const loading = ref(false)
  const payload = ref<RealtimeTodayPayload | null>(null)

  const totals = computed(() => payload.value?.totals || {})
  const effectiveDate = computed(() => String(payload.value?.effective_date || ''))
  const dayPnl = computed(() => Number(totals.value.day_pnl || 0))
  const dayPnlRate = computed(() => Number(totals.value.day_pnl_rate || 0))

  async function load() {
    loading.value = true
    try {
      const params = new URLSearchParams()
      const ledgerId = ledgerScopeStore.currentLedgerId
      if (ledgerId != null) params.set('ledger_id', String(ledgerId))
      const query = params.toString()
      payload.value = await api.get<RealtimeTodayPayload>(
        query ? `/api/realtime/today?${query}` : '/api/realtime/today',
        true,
      )
    } finally {
      loading.value = false
    }
  }

  function clear() {
    payload.value = null
  }

  return {
    loading,
    payload,
    totals,
    effectiveDate,
    dayPnl,
    dayPnlRate,
    load,
    clear,
  }
})
