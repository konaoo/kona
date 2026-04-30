import { ref } from 'vue'

type InvestLedgerSelectorEmit = {
  (event: 'select-ledger', ledgerId: number): void
  (event: 'manage'): void
}

export function createInvestLedgerSelectorController(emit: InvestLedgerSelectorEmit) {
  const showDropdown = ref(false)

  function toggleDropdown() {
    showDropdown.value = !showDropdown.value
  }

  function closeDropdown() {
    showDropdown.value = false
  }

  function selectLedger(ledgerId: number) {
    closeDropdown()
    emit('select-ledger', ledgerId)
  }

  function openManage() {
    closeDropdown()
    emit('manage')
  }

  return {
    showDropdown,
    toggleDropdown,
    closeDropdown,
    selectLedger,
    openManage
  }
}
