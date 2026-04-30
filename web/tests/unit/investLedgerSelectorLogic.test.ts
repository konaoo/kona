import { describe, expect, it, vi } from 'vitest'
import { createInvestLedgerSelectorController } from '../../src/components/business/InvestLedgerSelector.logic'

describe('InvestLedgerSelector logic', () => {
  it('切换下拉、选择账本并关闭下拉', () => {
    const emit = vi.fn()
    const controller = createInvestLedgerSelectorController(emit)

    controller.toggleDropdown()
    expect(controller.showDropdown.value).toBe(true)

    controller.selectLedger(2)
    expect(controller.showDropdown.value).toBe(false)
    expect(emit).toHaveBeenCalledWith('select-ledger', 2)
  })

  it('点击管理时关闭下拉并发出 manage 事件', () => {
    const emit = vi.fn()
    const controller = createInvestLedgerSelectorController(emit)

    controller.toggleDropdown()
    controller.openManage()

    expect(controller.showDropdown.value).toBe(false)
    expect(emit).toHaveBeenCalledWith('manage')
  })
})
