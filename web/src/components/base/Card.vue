<script setup lang="ts">
/**
 * Card - 卡片组件
 * 容器组件，用于分组和展示内容
 */

import { computed } from 'vue'

export interface CardProps {
  /** 是否显示边框 */
  border?: boolean
  /** 是否可悬停 */
  hoverable?: boolean
  /** 内边距 */
  padding?: 'none' | 'sm' | 'md' | 'lg'
  /** 背景层级 */
  level?: 0 | 1 | 2 | 3
  /** 圆角大小 */
  radius?: 'sm' | 'md' | 'lg' | 'xl'
  /** 点击整个卡片 */
  clickable?: boolean
}

const props = withDefaults(defineProps<CardProps>(), {
  border: true,
  hoverable: false,
  padding: 'md',
  level: 1,
  radius: 'lg',
  clickable: false
})

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

const cardClass = computed(() => {
  return [
    'card',
    `card-padding-${props.padding}`,
    `card-radius-${props.radius}`,
    `card-level-${props.level}`,
    {
      'card-border': props.border,
      'card-hoverable': props.hoverable,
      'card-clickable': props.clickable
    }
  ]
})

const handleClick = (e: MouseEvent) => {
  if (props.clickable || props.hoverable) {
    emit('click', e)
  }
}
</script>

<template>
  <div :class="cardClass" @click="handleClick">
    <slot />
  </div>
</template>

<style scoped>
/* ═══════════════════════════════════════════════════════════════
   CARD COMPONENT - 卡片组件样式
   ═══════════════════════════════════════════════════════════════ */

.card {
  /* Layout */
  display: block;
  width: 100%;

  /* Transition */
  transition: all var(--duration-base) var(--easing-default);
}

/* ───────────────────────────────────────────────────────────────
   CARD PADDING - 内边距变体
   ─────────────────────────────────────────────────────────────── */

.card-padding-none {
  padding: 0;
}

.card-padding-sm {
  padding: var(--space-3);
}

.card-padding-md {
  padding: var(--space-4);
}

.card-padding-lg {
  padding: var(--space-6);
}

/* ───────────────────────────────────────────────────────────────
   CARD RADIUS - 圆角变体
   ─────────────────────────────────────────────────────────────── */

.card-radius-sm {
  border-radius: var(--radius-sm);
}

.card-radius-md {
  border-radius: var(--radius-md);
}

.card-radius-lg {
  border-radius: var(--radius-lg);
}

.card-radius-xl {
  border-radius: var(--radius-xl);
}

/* ───────────────────────────────────────────────────────────────
   CARD LEVEL - 背景层级
   ─────────────────────────────────────────────────────────────── */

.card-level-0 {
  background: var(--bg);
}

.card-level-1 {
  background: var(--s1);
}

.card-level-2 {
  background: var(--s2);
}

.card-level-3 {
  background: var(--s3);
}

/* ───────────────────────────────────────────────────────────────
   CARD BORDER - 边框
   ─────────────────────────────────────────────────────────────── */

.card-border {
  border: 1px solid var(--border);
}

/* ───────────────────────────────────────────────────────────────
   CARD STATES - 交互状态
   ─────────────────────────────────────────────────────────────── */

.card-hoverable:hover,
.card-clickable:hover {
  border-color: var(--border-hover);
  box-shadow: var(--shadow-md);
  transform: translateY(-2px);
}

.card-clickable {
  cursor: pointer;
  user-select: none;
}

.card-clickable:active {
  transform: translateY(0);
}
</style>
