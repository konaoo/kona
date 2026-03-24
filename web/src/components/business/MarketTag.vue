<script setup lang="ts">
/**
 * MarketTag - 市场标签组件
 * 用于显示市场类型，带图标和颜色
 */

import { computed } from 'vue'
import type { MarketCode } from '@/types'

export interface MarketTagProps {
  /** 市场代码 */
  market: MarketCode
  /** 是否显示图标 */
  showIcon?: boolean
  /** 标签尺寸 */
  size?: 'sm' | 'md'
  /** 是否显示全称 */
  fullName?: boolean
}

const props = withDefaults(defineProps<MarketTagProps>(), {
  showIcon: true,
  size: 'md',
  fullName: false
})

const marketInfo = computed(() => {
  const info: Record<MarketCode, { name: string; icon: string; color: string; bg: string }> = {
    a: { name: 'A股', icon: '🇨🇳', color: 'var(--red)', bg: 'rgba(240, 90, 85, 0.15)' },
    hk: { name: '港股', icon: '🇭🇰', color: 'var(--gold)', bg: 'rgba(212, 175, 100, 0.15)' },
    us: { name: '美股', icon: '🇺🇸', color: 'var(--blue)', bg: 'rgba(91, 141, 239, 0.15)' },
    fund: { name: '基金', icon: '💼', color: 'var(--green)', bg: 'rgba(62, 207, 130, 0.15)' }
  }

  return info[props.market] || info.fund
})

const tagClass = computed(() => {
  return [
    'market-tag',
    `market-tag-${props.size}`
  ]
})

const tagStyle = computed(() => {
  return {
    color: marketInfo.value.color,
    backgroundColor: marketInfo.value.bg,
    borderColor: marketInfo.value.color + '30'
  }
})
</script>

<template>
  <span :class="tagClass" :style="tagStyle">
    <span v-if="showIcon" class="market-tag-icon">{{ marketInfo.icon }}</span>
    <span class="market-tag-text">{{ fullName ? marketInfo.name : marketInfo.name[0] }}</span>
  </span>
</template>

<style scoped>
/* ═══════════════════════════════════════════════════════════════
   MARKET TAG - 市场标签样式
   ═══════════════════════════════════════════════════════════════ */

.market-tag {
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);
  padding: var(--space-1) var(--space-2);
  border: 1px solid transparent;
  border-radius: var(--radius-sm);
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  line-height: 1;
  white-space: nowrap;
  transition: all var(--duration-base) var(--easing-default);
}

.market-tag-sm {
  padding: 2px var(--space-1);
  font-size: 9px;
  gap: 2px;
}

.market-tag-icon {
  font-size: 1.1em;
  line-height: 1;
}

.market-tag-text {
  line-height: 1;
}
</style>
