<script setup lang="ts">
/**
 * Tag - 标签组件
 * 用于显示市场类型、资产分类等标识
 */

import { computed } from 'vue'

export interface TagProps {
  /** 标签类型 */
  type?: 'hk' | 'us' | 'a' | 'fund' | 'bond' | 'cash' | 'custom'
  /** 自定义文本 */
  text?: string
  /** 自定义颜色 */
  color?: string
  /** 是否可关闭 */
  closable?: boolean
  /** 标签尺寸 */
  size?: 'sm' | 'md'
}

const props = withDefaults(defineProps<TagProps>(), {
  type: 'fund',
  text: '',
  color: '',
  closable: false,
  size: 'md'
})

const emit = defineEmits<{
  close: []
}>()

const tagClass = computed(() => {
  return [
    'tag',
    `tag-${props.type}`,
    `tag-${props.size}`,
    {
      'tag-closable': props.closable
    }
  ]
})

const tagStyle = computed(() => {
  if (props.color) {
    return {
      backgroundColor: `${props.color}15`,
      color: props.color,
      borderColor: `${props.color}30`
    }
  }
  return {}
})

const displayText = computed(() => {
  if (props.text) {
    return props.text
  }

  const typeMap: Record<string, string> = {
    hk: '港股',
    us: '美股',
    a: 'A股',
    fund: '基金',
    bond: '债券',
    cash: '现金',
    custom: '自定义'
  }

  return typeMap[props.type] || '未知'
})

const handleClose = (e: MouseEvent) => {
  e.stopPropagation()
  emit('close')
}
</script>

<template>
  <span :class="tagClass" :style="tagStyle">
    <span class="tag-text">{{ displayText }}</span>
    <span v-if="closable" class="tag-close" @click="handleClose">×</span>
  </span>
</template>

<style scoped>
/* ═══════════════════════════════════════════════════════════════
   TAG COMPONENT - 标签组件样式
   ═══════════════════════════════════════════════════════════════ */

.tag {
  /* Layout */
  display: inline-flex;
  align-items: center;
  gap: var(--space-1);

  /* Typography */
  font-size: var(--font-size-xs);
  font-weight: var(--font-weight-medium);
  line-height: 1;
  white-space: nowrap;

  /* Spacing */
  padding: var(--space-1) var(--space-2);

  /* Border & Radius */
  border: 1px solid transparent;
  border-radius: var(--radius-sm);

  /* Transition */
  transition: all var(--duration-base) var(--easing-default);
}

/* ───────────────────────────────────────────────────────────────
   TAG SIZES - 尺寸变体
   ─────────────────────────────────────────────────────────────── */

.tag-sm {
  padding: 2px var(--space-1);
  font-size: 9px;
}

.tag-md {
  padding: var(--space-1) var(--space-2);
  font-size: var(--font-size-xs);
}

/* ───────────────────────────────────────────────────────────────
   TAG TYPES - 类型变体
   ─────────────────────────────────────────────────────────────── */

.tag-hk {
  background: rgba(212, 175, 100, 0.15);
  color: var(--gold);
  border-color: rgba(212, 175, 100, 0.3);
}

.tag-us {
  background: rgba(91, 141, 239, 0.15);
  color: var(--blue);
  border-color: rgba(91, 141, 239, 0.3);
}

.tag-a {
  background: rgba(240, 90, 85, 0.15);
  color: var(--red);
  border-color: rgba(240, 90, 85, 0.3);
}

.tag-fund {
  background: rgba(62, 207, 130, 0.15);
  color: var(--green);
  border-color: rgba(62, 207, 130, 0.3);
}

.tag-bond {
  background: rgba(91, 141, 239, 0.15);
  color: var(--blue);
  border-color: rgba(91, 141, 239, 0.3);
}

.tag-cash {
  background: var(--s2);
  color: var(--sub);
  border-color: var(--border);
}

.tag-custom {
  background: var(--s2);
  color: var(--sub);
  border-color: var(--border);
}

/* ───────────────────────────────────────────────────────────────
   TAG CLOSE BUTTON - 关闭按钮
   ─────────────────────────────────────────────────────────────── */

.tag-closable {
  padding-right: var(--space-1);
}

.tag-close {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 14px;
  height: 14px;
  margin-left: var(--space-1);
  font-size: 14px;
  line-height: 1;
  cursor: pointer;
  border-radius: var(--radius-sm);
  transition: all var(--duration-base) var(--easing-default);
}

.tag-close:hover {
  background: var(--border);
}

.tag-text {
  display: inline-block;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
