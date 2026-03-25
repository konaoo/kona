import { ref } from 'vue'
import { defineStore } from 'pinia'

export const useLedgerScopeStore = defineStore('ledgerScope', () => {
  const currentLedgerId = ref<number | null>(null)

  function setCurrentLedgerId(ledgerId: number | null) {
    currentLedgerId.value = ledgerId == null ? null : Number(ledgerId)
  }

  return {
    currentLedgerId,
    setCurrentLedgerId,
  }
})
