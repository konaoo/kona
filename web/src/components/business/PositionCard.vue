<script setup lang="ts">
/**
 * PositionCard - 持仓卡片组件
 * 用于展示单个持仓的详细信息
 */

import { computed } from 'vue'
import type { PositionRow } from '@/types'

export interface PositionCardProps {
  /** 持仓数据 */
  position: PositionRow
  /** 是否显示市场标签 */
  showMarket?: boolean
  /** 是否显示代码 */
  showCode?: boolean
  /** 是否可点击 */
  clickable?: boolean
  /** 卡片尺寸 */
  size?: 'sm' | 'md' | 'lg'
}

const props = withDefaults(defineProps<PositionCardProps>(), {
  showMarket: true,
  showCode: true,
  clickable: true,
  size: 'md'
})

const emit = defineEmits<{
  click: [position: PositionRow]
}>()

const cardClass = computed(() => {
  return [
    'position-card',
    `position-card-${props.size}`,
    {
      'position-card-clickable': props.clickable
    }
  ]
})

const pnlClass = computed(() => {
  if (props.position.dayPnl > 0) return 'text-up'
  if (props.position.dayPnl < 0) return 'text-down'
  return 'text-muted'
})

const totalPnLClass = computed(() => {
  if (props.position.totalPnl > 0) return 'text-up'
  if (props.position.totalPnl < 0) return 'text-down'
  return 'text-muted'
})

const handleClick = () => {
  if (props.clickable) {
    emit('click', props.position)
  }
}
</script>

<template>
  <div :class="cardClass" @click="handleClick">
    <!-- 头部：名称和市场标签 -->
    <div class="position-card-header">
      <div class="position-card-name">
        <span class="name-text">{{ position.name || position.code }}</span>
        <span v-if="showCode" class="name-code">{{ position.code }}</span>
      </div>
      <Tag v-if="showMarket" :type="position.market === 'fund' ? 'fund' : position.market" size="sm" />
    </div>

    <!-- 主要数据：持有金额和成本 -->
    <div class="position-card-body">
      <div class="position-card-value">
        <div class="value-label">持有金额</div>
        <div class="value-amount mono">
          {{ position.currency === 'CNY' ? '¥' : position.currency === 'HKD' ? '$' : 'US$' }}
          {{ position.value.toLocaleString('zh-CN', { minimumFractionDigits: 2, maximumFractionDigits: 2 }) }}
        </div>
      </div>

      <div class="position-card-cost">
        <div class="cost-label">成本</div>
        <div class="cost-value mono">
          ¥{{ position.displayCostPrice?.toFixed(2) || position.costPrice?.toFixed(2) || '-' }}
        </div>
        <div class="cost-divider">/</div>
        <div class="cost-value mono">
          ¥{{ position.currentPrice?.toFixed(2) || '-' }}
        </div>
      </div>
    </div>

    <!-- 底部：盈亏信息 -->
    <div class="position-card-footer">
      <div class="pnl-item">
        <span class="pnl-label">当日盈亏</span>
        <span :class="['pnl-value', 'mono', pnlClass]">
          {{ position.dayPnl >= 0 ? '+' : '' }}{{ position.dayPnl.toFixed(2) }}
          <template v-if="position.dayPnlRate !== 0">
            ({{ position.dayPnlRate >= 0 ? '+' : '' }}{{ position.dayPnlRate.toFixed(2) }}%)
          </template>
        </span>
      </div>

      <div class="pnl-item">
        <span class="pnl-label">累计盈亏</span>
        <span :class="['pnl-value', 'mono', totalPnLClass]">
          {{ position.totalPnl >= 0 ? '+' : '' }}{{ position.totalPnl.toFixed(2) }}
          <template v-if="position.totalPnlRate !== 0">
            ({{ position.totalPnlRate >= 0 ? '+' : '' }}{{ position.totalPnlRate.toFixed(2) }}%)
          </template>
        </span>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ═══════════════════════════════════════════════════════════════
   POSITION CARD - 持仓卡片样式
   ═══════════════════════════════════════════════════════════════ */

.position-card {
  background: var(--s1);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
  transition: all var(--duration-base) var(--easing-default);
}

.position-card-clickable {
  cursor: pointer;
  user-select: none;
}

.position-card-clickable:hover {
  border-color: var(--border-hover);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

/* ───────────────────────────────────────────────────────────────
   HEADER - 头部区域
   ─────────────────────────────────────────────────────────────── */

.position-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-3);
}

.position-card-name {
  flex: 1;
  min-width: 0;
}

.name-text {
  display: block;
  font-size: var(--font-size-md);
  font-weight: var(--font-weight-semibold);
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.name-code {
  display: block;
  font-size: var(--font-size-xs);
  color: var(--sub);
  margin-top: 2px;
}

/* ───────────────────────────────────────────────────────────────
   BODY - 主要内容区
   ─────────────────────────────────────────────────────────────── */

.position-card-body {
  margin-bottom: var(--space-3);
}

.position-card-value {
  margin-bottom: var(--space-3);
}

.value-label {
  font-size: var(--font-size-xs);
  color: var(--muted);
  margin-bottom: var(--space-1);
}

.value-amount {
  font-size: var(--font-size-xl);
  font-weight: var(--font-weight-semibold);
  color: var(--text);
  line-height: 1.2;
}

.position-card-cost {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.cost-label {
  font-size: var(--font-size-xs);
  color: var(--muted);
}

.cost-value {
  font-size: var(--font-size-sm);
  color: var(--sub);
}

.cost-divider {
  color: var(--muted);
  font-size: var(--font-size-sm);
}

/* ───────────────────────────────────────────────────────────────
   FOOTER - 底部盈亏区
   ─────────────────────────────────────────────────────────────── */

.position-card-footer {
  display: flex;
  justify-content: space-between;
  padding-top: var(--space-3);
  border-top: 1px solid var(--border);
}

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
   SIZE VARIANTS - 尺寸变体
   ─────────────────────────────────────────────────────────────── */

.position-card-sm .value-amount {
  font-size: var(--font-size-lg);
}

.position-card-sm .pnl-value {
  font-size: var(--font-size-xs);
}

.position-card-lg .value-amount {
  font-size: var(--font-size-2xl);
}

.position-card-lg .pnl-value {
  font-size: var(--font-size-base);
}
</style>
