<script setup lang="ts">
import type { Ledger } from '@/stores/ledgerScope'
import { createInvestLedgerSelectorController } from './InvestLedgerSelector.logic'

defineProps<{
  ledgers: Ledger[]
  currentLedgerId: number | null
  currentLedgerName: string
  isDefaultLedger: (ledger: Ledger) => boolean
}>()

const emit = defineEmits<{
  (event: 'select-ledger', ledgerId: number): void
  (event: 'manage'): void
}>()

const { showDropdown, toggleDropdown, closeDropdown, selectLedger, openManage } =
  createInvestLedgerSelectorController(emit)
</script>

<template>
  <div v-if="ledgers.length > 0" class="ledger-selector-bar">
    <div class="ledger-trigger-wrapper">
      <button class="ledger-trigger" :class="{ open: showDropdown }" @click="toggleDropdown">
        <span class="ledger-trigger-name">{{ currentLedgerName }}</span>
        <svg
          class="ledger-chevron"
          :class="{ rotated: showDropdown }"
          width="12"
          height="12"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          stroke-width="2.5"
          stroke-linecap="round"
        >
          <polyline points="6 9 12 15 18 9" />
        </svg>
      </button>

      <Transition name="dropdown">
        <div v-if="showDropdown" class="ledger-dropdown">
          <div class="ledger-dropdown-backdrop" @click="closeDropdown"></div>
          <div class="ledger-dropdown-card">
            <div
              v-for="ledger in ledgers"
              :key="ledger.id"
              class="ledger-menu-item"
              :class="{ active: ledger.id === currentLedgerId }"
              @click="selectLedger(ledger.id)"
            >
              <span class="ledger-menu-name">{{ ledger.name }}</span>
              <span v-if="isDefaultLedger(ledger)" class="ledger-menu-badge">默认</span>
              <svg
                v-if="ledger.id === currentLedgerId"
                class="ledger-menu-check"
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2.5"
                stroke-linecap="round"
              >
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </div>
            <div class="ledger-menu-divider"></div>
            <div class="ledger-menu-item manage" @click="openManage">
              <svg
                width="16"
                height="16"
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                stroke-width="2"
                stroke-linecap="round"
              >
                <circle cx="12" cy="12" r="3" />
                <path
                  d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"
                />
              </svg>
              <span>管理账本</span>
            </div>
          </div>
        </div>
      </Transition>
    </div>
  </div>
</template>

<style scoped>
.ledger-selector-bar {
  margin-bottom: 20px;
}

.ledger-trigger-wrapper {
  position: relative;
  display: inline-block;
}

.ledger-trigger {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border: 1px solid rgba(188, 149, 82, 0.15);
  border-radius: 999px;
  background: rgba(188, 149, 82, 0.04);
  color: var(--text);
  font-size: 13px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.15s;
}

.ledger-trigger:hover,
.ledger-trigger.open {
  border-color: rgba(188, 149, 82, 0.3);
  background: rgba(188, 149, 82, 0.08);
}

.ledger-trigger-name {
  max-width: 140px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ledger-chevron {
  color: var(--muted);
  transition: transform 0.2s;
  flex-shrink: 0;
}

.ledger-chevron.rotated {
  transform: rotate(180deg);
}

.ledger-dropdown {
  position: absolute;
  top: calc(100% + 8px);
  left: 0;
  z-index: 100;
}

.ledger-dropdown-backdrop {
  position: fixed;
  inset: 0;
  z-index: -1;
}

.ledger-dropdown-card {
  min-width: 180px;
  max-width: 260px;
  background: var(--s1, #14171f);
  border: 1px solid rgba(188, 149, 82, 0.2);
  border-radius: 14px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.4);
  overflow: hidden;
}

.ledger-menu-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 11px 14px;
  cursor: pointer;
  transition: background 0.12s;
}

.ledger-menu-item:hover {
  background: rgba(188, 149, 82, 0.06);
}

.ledger-menu-item.active {
  background: rgba(188, 149, 82, 0.1);
}

.ledger-menu-item.active .ledger-menu-name {
  color: #cdb47c;
}

.ledger-menu-name {
  flex: 1;
  font-size: 14px;
  font-weight: 600;
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ledger-menu-badge {
  font-size: 11px;
  font-weight: 600;
  color: #cdb47c;
  border: 1px solid rgba(205, 180, 124, 0.3);
  background: rgba(205, 180, 124, 0.08);
  padding: 2px 7px;
  border-radius: 999px;
  white-space: nowrap;
}

.ledger-menu-check {
  color: #cdb47c;
  flex-shrink: 0;
}

.ledger-menu-divider {
  height: 1px;
  margin: 0 10px;
  background: rgba(255, 255, 255, 0.06);
}

.ledger-menu-item.manage {
  gap: 10px;
  color: var(--text);
}

.ledger-menu-item.manage svg {
  color: var(--muted);
}

.dropdown-enter-active {
  transition: all 0.18s ease-out;
}

.dropdown-leave-active {
  transition: all 0.12s ease-in;
}

.dropdown-enter-from {
  opacity: 0;
  transform: translateY(-4px);
}

.dropdown-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
