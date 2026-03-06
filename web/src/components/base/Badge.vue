<script setup lang="ts">
/**
 * Badge - 徽章组件
 * 用于显示涨跌幅、状态标识等
 */

import { computed } from 'vue'

export interface BadgeProps {
  /** 徽章类型 */
  type?: 'up' | 'down' | 'neutral' | 'primary' | 'success' | 'warning' | 'danger'
  /** 数值（自动判断涨跌） */
  value?: number
  /** 是否显示百分比符号 */
  percent?: boolean
  /** 自定义文本 */
  text?: string
}

const props = withDefaults(defineProps<BadgeProps>(), {
  type: 'neutral',
  value: 0,
  percent: true,
  text: ''
})

const badgeClass = computed(() => {
  // 如果提供了value，根据数值正负自动判断类型
  if (props.value !== 0 && !props.text) {
    return props.value > 0 ? 'badge badge-up' : 'badge badge-down'
  }

  return `badge badge-${props.type}`
})

const displayText = computed(() => {
  if (props.text) {
    return props.text
  }

  const prefix = props.value > 0 ? '+' : ''
  const suffix = props.percent ? '%' : ''
  return `${prefix}${props.value}${suffix}`
})
</script>

<template>
  <span :class="badgeClass">
    {{ displayText }}
  </span>
</template>

<style scoped>
/* ═══════════════════════════════════════════════════════════════
   BADGE COMPONENT - 徽章组件样式
   ═══════════════════════════════════════════════════════════════ */

.badge {
  /* Layout */
  display: inline-flex;
  align-items: center;
  justify-content: center;

  /* Typography */
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-semibold);
  line-height: 1;
  white-space: nowrap;

  /* Spacing */
  padding: var(--space-1) var(--space-2);

  /* Border & Radius */
  border-radius: var(--radius-sm);

  /* Transition */
  transition: all var(--duration-base) var(--easing-default);
}

/* ───────────────────────────────────────────────────────────────
   BADGE TYPES - 类型变体
   ─────────────────────────────────────────────────────────────── */

.badge-up {
  background: rgba(240, 90, 85, 0.15);
  color: var(--red);
}

.badge-down {
  background: rgba(62, 207, 130, 0.15);
  color: var(--green);
}

.badge-neutral {
  background: var(--s2);
  color: var(--muted);
}

.badge-primary {
  background: rgba(91, 141, 239, 0.15);
  color: var(--blue);
}

.badge-success {
  background: rgba(62, 207, 130, 0.15);
  color: var(--green);
}

.badge-warning {
  background: rgba(212, 175, 100, 0.15);
  color: var(--gold);
}

.badge-danger {
  background: rgba(240, 90, 85, 0.15);
  color: var(--red);
}
</style>
