<script setup lang="ts">
/**
 * AssetSummary - 资产摘要组件
 * 用于展示总资产、盈亏等关键指标
 */

import { computed } from 'vue'

export interface AssetSummaryProps {
  /** 总资产 */
  totalAsset: number
  /** 当日盈亏 */
  dayPnL: number
  /** 当日盈亏比例 */
  dayPnLRate: number
  /** 累计盈亏 */
  totalPnL: number
  /** 累计盈亏比例 */
  totalPnLRate: number
  /** 币种 */
  currency?: string
  /** 是否显示图标 */
  showIcon?: boolean
  /** 布局方式 */
  layout?: 'horizontal' | 'vertical' | 'compact'
}

const props = withDefaults(defineProps<AssetSummaryProps>(), {
  currency: 'CNY',
  showIcon: true,
  layout: 'horizontal'
})

const currencySymbol = computed(() => {
  const symbols: Record<string, string> = {
    CNY: '¥',
    HKD: '$',
    USD: 'US$'
  }
  return symbols[props.currency] || props.currency
})

const dayPnLClass = computed(() => {
  if (props.dayPnL > 0) return 'text-up'
  if (props.dayPnL < 0) return 'text-down'
  return ''
})

const totalPnLClass = computed(() => {
  if (props.totalPnL > 0) return 'text-up'
  if (props.totalPnL < 0) return 'text-down'
  return ''
})
</script>

<template>
  <div :class="['asset-summary', `asset-summary-${layout}`]">
    <!-- 主资产显示 -->
    <div class="asset-main">
      <div v-if="showIcon" class="asset-icon">💰</div>
      <div class="asset-info">
        <div class="asset-label">总资产</div>
        <div class="asset-value mono">
          {{ currencySymbol }}{{ totalAsset.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
        </div>
      </div>
    </div>

    <!-- 盈亏信息 -->
    <div class="asset-pnl">
      <div class="pnl-item">
        <span class="pnl-label">当日盈亏</span>
        <span :class="['pnl-value', 'mono', dayPnLClass]">
          {{ dayPnL >= 0 ? '+' : '' }}{{ (dayPnL || 0).toFixed(2) }}
          <template v-if="dayPnLRate !== 0">
            ({{ dayPnLRate >= 0 ? '+' : '' }}{{ (dayPnLRate || 0).toFixed(2) }}%)
          </template>
        </span>
      </div>

      <div class="pnl-item">
        <span class="pnl-label">累计盈亏</span>
        <span :class="['pnl-value', 'mono', totalPnLClass]">
          {{ totalPnL >= 0 ? '+' : '' }}{{ (totalPnL || 0).toFixed(2) }}
          <template v-if="totalPnLRate !== 0">
            ({{ totalPnLRate >= 0 ? '+' : '' }}{{ (totalPnLRate || 0).toFixed(2) }}%)
          </template>
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ═══════════════════════════════════════════════════════════════
   ASSET SUMMARY - 资产摘要样式
   ═══════════════════════════════════════════════════════════════ */

.asset-summary {
  background: var(--s1);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
}

/* ───────────────────────────────────────────────────────────────
   HORIZONTAL LAYOUT - 水平布局
   ─────────────────────────────────────────────────────────────── */

.asset-summary-horizontal {
  display: flex;
  align-items: center;
  gap: var(--space-6);
}

.asset-summary-horizontal .asset-main {
  flex: 0 0 auto;
}

.asset-summary-horizontal .asset-pnl {
  flex: 1;
  display: flex;
  gap: var(--space-6);
}

/* ───────────────────────────────────────────────────────────────
   VERTICAL LAYOUT - 垂直布局
   ─────────────────────────────────────────────────────────────── */

.asset-summary-vertical {
  display: flex;
  flex-direction: column;
  gap: var(--space-4);
}

.asset-summary-vertical .asset-main {
  text-align: center;
  justify-content: center;
}

.asset-summary-vertical .asset-pnl {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

/* ───────────────────────────────────────────────────────────────
   COMPACT LAYOUT - 紧凑布局
   ─────────────────────────────────────────────────────────────── */

.asset-summary-compact {
  display: flex;
  align-items: center;
  gap: var(--space-4);
  padding: var(--space-3);
}

.asset-summary-compact .asset-main {
  flex: 0 0 auto;
}

.asset-summary-compact .asset-pnl {
  flex: 1;
  display: flex;
  gap: var(--space-4);
}

/* ───────────────────────────────────────────────────────────────
   ASSET MAIN - 主资产区域
   ─────────────────────────────────────────────────────────────── */

.asset-main {
  display: flex;
  align-items: center;
  gap: var(--space-3);
}

.asset-icon {
  font-size: 32px;
  line-height: 1;
  flex-shrink: 0;
}

.asset-info {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.asset-label {
  font-size: var(--font-size-xs);
  color: var(--muted);
}

.asset-value {
  font-size: var(--font-size-2xl);
  font-weight: var(--font-weight-bold);
  color: var(--text);
  line-height: 1.2;
}

/* ───────────────────────────────────────────────────────────────
   PNL - 盈亏区域
   ─────────────────────────────────────────────────────────────── */

.pnl-item {
  display: flex;
  flex-direction: column;
  gap: var(--space-1);
}

.pnl-label {
  font-size: var(--font-size-xs);
  color: var(--muted);
}

.pnl-value {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

/* ───────────────────────────────────────────────────────────────
   RESPONSIVE - 响应式
   ─────────────────────────────────────────────────────────────── */

@media (max-width: 768px) {
  .asset-summary-horizontal {
    flex-direction: column;
    align-items: flex-start;
    gap: var(--space-4);
  }

  .asset-summary-horizontal .asset-pnl {
    width: 100%;
    flex-direction: column;
    gap: var(--space-3);
  }
}
</style>
