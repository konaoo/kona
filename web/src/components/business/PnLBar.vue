<script setup lang="ts">
/**
 * PnLBar - 盈亏进度条组件
 * 用于可视化展示盈亏比例
 */

import { computed } from 'vue'

export interface PnLBarProps {
  /** 盈亏金额 */
  value: number
  /** 总金额 */
  total: number
  /** 是否显示标签 */
  showLabel?: boolean
  /** 进度条高度 */
  height?: number
  /** 是否显示数值 */
  showValue?: boolean
  /** 是否显示百分比 */
  showPercent?: boolean
  /** 是否显示颜色动画 */
  animated?: boolean
}

const props = withDefaults(defineProps<PnLBarProps>(), {
  showLabel: true,
  height: 8,
  showValue: true,
  showPercent: false,
  animated: true
})

const pnlRate = computed(() => {
  if (props.total === 0) return 0
  return (props.value / props.total) * 100
})

const pnlClass = computed(() => {
  if (props.value > 0) return 'pnl-up'
  if (props.value < 0) return 'pnl-down'
  return 'pnl-neutral'
})

const pnlColor = computed(() => {
  if (props.value > 0) return 'var(--red)'
  if (props.value < 0) return 'var(--green)'
  return 'var(--muted)'
})

const absRate = computed(() => {
  return Math.abs(pnlRate.value)
})

const barStyle = computed(() => {
  return {
    width: `${absRate.value}%`,
    height: `${props.height}px`,
    backgroundColor: pnlColor.value
  }
})

const formattedValue = computed(() => {
  const prefix = props.value >= 0 ? '+' : ''
  return `${prefix}${props.value.toFixed(2)}`
})
</script>

<template>
  <div class="pnl-bar">
    <div v-if="showLabel || showValue" class="pnl-header">
      <div v-if="showLabel" class="pnl-label">
        <slot name="label">盈亏比例</slot>
      </div>
      <div v-if="showValue" :class="['pnl-value', 'mono', pnlClass]">
        {{ formattedValue }}
        <template v-if="showPercent">
          ({{ absRate.toFixed(2) }}%)
        </template>
      </div>
    </div>

    <div class="pnl-track">
      <div
        :class="['pnl-fill', { 'pnl-animated': animated }]"
        :style="barStyle"
      />
    </div>
  </div>
</template>

<style scoped>
/* ═══════════════════════════════════════════════════════════════
   PNL BAR - 盈亏进度条样式
   ═══════════════════════════════════════════════════════════════ */

.pnl-bar {
  width: 100%;
}

/* ───────────────────────────────────────────────────────────────
   HEADER - 头部
   ─────────────────────────────────────────────────────────────── */

.pnl-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-2);
}

.pnl-label {
  font-size: var(--font-size-sm);
  color: var(--sub);
}

.pnl-value {
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-medium);
}

.pnl-up {
  color: var(--red);
}

.pnl-down {
  color: var(--green);
}

.pnl-neutral {
  color: var(--muted);
}

/* ───────────────────────────────────────────────────────────────
   TRACK - 轨道
   ─────────────────────────────────────────────────────────────── */

.pnl-track {
  width: 100%;
  background: var(--s1);
  border-radius: var(--radius-sm);
  overflow: hidden;
}

/* ───────────────────────────────────────────────────────────────
   FILL - 填充
   ─────────────────────────────────────────────────────────────── */

.pnl-fill {
  border-radius: var(--radius-sm);
  transition: width var(--duration-slow) var(--easing-default);
}

.pnl-animated {
  animation: pnl-pulse 2s ease-in-out infinite;
}

@keyframes pnl-pulse {
  0%, 100% {
    opacity: 1;
  }
  50% {
    opacity: 0.8;
  }
}
</style>
