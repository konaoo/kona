<script setup lang="ts">
/**
 * RankingCard - 排行榜卡片组件
 * 用于展示涨跌幅排行、收益排行等
 */

import { computed } from 'vue'

export interface RankingItem {
  code: string
  name?: string
  value: number
  change: number
  changeRate: number
}

export interface RankingCardProps {
  /** 标题 */
  title: string
  /** 排行榜数据 */
  items: RankingItem[]
  /** 排行榜类型 */
  type?: 'gain' | 'loss' | 'volume' | 'turnover'
  /** 显示数量 */
  limit?: number
  /** 是否显示排名 */
  showRank?: boolean
  /** 卡片尺寸 */
  size?: 'sm' | 'md' | 'lg'
}

const props = withDefaults(defineProps<RankingCardProps>(), {
  type: 'gain',
  limit: 5,
  showRank: true,
  size: 'md'
})

const emit = defineEmits<{
  itemClick: [item: RankingItem]
}>()

const titleIcon = computed(() => {
  const icons = {
    gain: '📈',
    loss: '📉',
    volume: '📊',
    turnover: '💰'
  }
  return icons[props.type]
})

const displayItems = computed(() => {
  return props.items.slice(0, props.limit)
})

const changeColorClass = computed(() => {
  return props.type === 'gain' ? 'text-up' : 'text-down'
})

const handleItemClick = (item: RankingItem) => {
  emit('itemClick', item)
}
</script>

<template>
  <div class="ranking-card">
    <div class="ranking-card-header">
      <div class="ranking-card-title">
        <span class="title-icon">{{ titleIcon }}</span>
        <span class="title-text">{{ title }}</span>
      </div>
      <slot name="extra" />
    </div>

    <div class="ranking-card-list">
      <div
        v-for="(item, index) in displayItems"
        :key="item.code"
        class="ranking-item"
        @click="handleItemClick(item)"
      >
        <div v-if="showRank" class="ranking-rank" :class="{ 'rank-top': index < 3 }">
          {{ index + 1 }}
        </div>

        <div class="ranking-info">
          <div class="ranking-name">
            {{ item.name || item.code }}
          </div>
          <div class="ranking-code mono">{{ item.code }}</div>
        </div>

        <div class="ranking-value">
          <div class="value-amount mono">{{ item.value.toLocaleString() }}</div>
          <div :class="['value-change', 'mono', changeColorClass]">
            {{ item.change >= 0 ? '+' : '' }}{{ item.changeRate.toFixed(2) }}%
          </div>
        </div>
      </div>
    </div>

    <div v-if="items.length === 0" class="ranking-empty">
      <div class="empty-icon">📭</div>
      <div class="empty-text">暂无数据</div>
    </div>
  </div>
</template>

<style scoped>
/* ═══════════════════════════════════════════════════════════════
   RANKING CARD - 排行榜卡片样式
   ═══════════════════════════════════════════════════════════════ */

.ranking-card {
  background: var(--s1);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  padding: var(--space-4);
}

/* ───────────────────────────────────────────────────────────────
   HEADER - 头部
   ─────────────────────────────────────────────────────────────── */

.ranking-card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--space-4);
}

.ranking-card-title {
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.title-icon {
  font-size: var(--font-size-lg);
}

.title-text {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-semibold);
  color: var(--text);
}

/* ───────────────────────────────────────────────────────────────
   LIST - 列表
   ─────────────────────────────────────────────────────────────── */

.ranking-card-list {
  display: flex;
  flex-direction: column;
  gap: var(--space-3);
}

.ranking-item {
  display: flex;
  align-items: center;
  gap: var(--space-3);
  padding: var(--space-3);
  background: var(--s2);
  border-radius: var(--radius-md);
  cursor: pointer;
  transition: all var(--duration-base) var(--easing-default);
  user-select: none;
}

.ranking-item:hover {
  background: var(--s3);
  transform: translateX(4px);
}

/* ───────────────────────────────────────────────────────────────
   RANK - 排名
   ─────────────────────────────────────────────────────────────── */

.ranking-rank {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  font-size: var(--font-size-sm);
  font-weight: var(--font-weight-semibold);
  color: var(--muted);
  background: var(--s1);
  border-radius: var(--radius-sm);
  flex-shrink: 0;
}

.ranking-rank.rank-top {
  background: linear-gradient(135deg, var(--gold), var(--red));
  color: white;
}

/* ───────────────────────────────────────────────────────────────
   INFO - 信息区
   ─────────────────────────────────────────────────────────────── */

.ranking-info {
  flex: 1;
  min-width: 0;
}

.ranking-name {
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ranking-code {
  font-size: var(--font-size-xs);
  color: var(--sub);
  margin-top: 2px;
}

/* ───────────────────────────────────────────────────────────────
   VALUE - 数值区
   ─────────────────────────────────────────────────────────────── */

.ranking-value {
  text-align: right;
  flex-shrink: 0;
}

.value-amount {
  font-size: var(--font-size-sm);
  color: var(--text);
  margin-bottom: 2px;
}

.value-change {
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
}

/* ───────────────────────────────────────────────────────────────
   EMPTY - 空状态
   ─────────────────────────────────────────────────────────────── */

.ranking-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--space-8) var(--space-4);
  color: var(--muted);
}

.empty-icon {
  font-size: 48px;
  margin-bottom: var(--space-3);
  opacity: 0.5;
}

.empty-text {
  font-size: var(--font-size-sm);
}
</style>
