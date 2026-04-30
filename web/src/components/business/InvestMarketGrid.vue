<script setup lang="ts">
type MarketCard = {
  name: string
  icon: string
  mv: number
  dayPnl: number
  dayRate: number
  dayPnlEnabled: boolean
  totalPnl: number
  totalRate: number
}

defineProps<{
  marketCards: MarketCard[]
  masked: (text: string) => string
  formatCurrency: (value: number, signed?: boolean, integerOnly?: boolean) => string
  valueClass: (value: number) => string
  formatPct: (value: number) => string
}>()
</script>

<template>
  <div class="market-grid">
    <div v-for="m in marketCards" :key="m.name" class="market-card">
      <div class="m-header">
        <div class="m-title">
          <span class="m-icon">{{ m.icon }}</span>
          <span class="m-name">{{ m.name }}</span>
        </div>
        <div class="m-mv">{{ masked(formatCurrency(m.mv)) }}</div>
      </div>
      <div class="m-stats">
        <div class="ms-item">
          <div class="ms-lbl">当日盈亏</div>
          <div class="ms-val-group" :class="m.dayPnlEnabled ? valueClass(m.dayPnl) : ''">
            <div class="ms-amt">{{ m.dayPnlEnabled ? masked(formatCurrency(m.dayPnl, true, true)) : '--' }}</div>
            <div class="ms-pct">{{ m.dayPnlEnabled ? formatPct(m.dayRate) : '--' }}</div>
          </div>
        </div>
        <div class="ms-item">
          <div class="ms-lbl">累计盈亏</div>
          <div class="ms-val-group" :class="valueClass(m.totalPnl)">
            <div class="ms-amt">{{ masked(formatCurrency(m.totalPnl, true, true)) }}</div>
            <div class="ms-pct">{{ formatPct(m.totalRate) }}</div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.market-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 32px;
}

.market-card {
  background: var(--s1);
  border: 1px solid var(--border);
  border-radius: 20px;
  padding: 18px;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.market-card:hover {
  border-color: rgba(91, 141, 239, 0.3);
  transform: translateY(-2px);
  background: var(--surface-faint);
}

.m-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.m-title {
  display: flex;
  align-items: center;
  gap: 8px;
}

.m-icon {
  font-size: 14px;
}

.m-name {
  font-size: 13px;
  font-weight: 700;
  color: var(--text);
  opacity: 0.9;
}

.m-mv {
  font-family: 'JetBrains Mono', monospace;
  font-size: 11px;
  font-weight: 600;
  color: var(--muted);
}

.m-stats {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.ms-item {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.ms-lbl {
  font-size: 10px;
  color: var(--muted);
  font-weight: 600;
  text-transform: uppercase;
}

.ms-val-group {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.ms-amt {
  font-family: 'JetBrains Mono', monospace;
  font-size: 12px;
  font-weight: 700;
  white-space: nowrap;
}

.ms-pct {
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  font-weight: 600;
  opacity: 0.85;
}

.ms-val-group.up {
  color: var(--red);
}

.ms-val-group.dn {
  color: var(--green);
}

:global([data-theme='light']) .market-card {
  box-shadow: 0 14px 34px rgba(15, 23, 42, 0.06);
}

@media (max-width: 900px) {
  .market-grid {
    grid-template-columns: 1fr 1fr;
  }
}
</style>
