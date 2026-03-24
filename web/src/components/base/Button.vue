<script setup lang="ts">
/**
 * Button - 按钮组件
 * 基础交互组件，支持多种样式和状态
 */

import { computed } from 'vue'

export interface ButtonProps {
  /** 按钮类型 */
  type?: 'primary' | 'secondary' | 'ghost' | 'danger'
  /** 按钮尺寸 */
  size?: 'sm' | 'md' | 'lg'
  /** 是否禁用 */
  disabled?: boolean
  /** 是否加载中 */
  loading?: boolean
  /** 按钮宽度 */
  block?: boolean
  /** 悬停提升效果 */
  hoverLift?: boolean
  /** 脉冲动画 */
  pulse?: boolean
}

const props = withDefaults(defineProps<ButtonProps>(), {
  type: 'primary',
  size: 'md',
  disabled: false,
  loading: false,
  block: false,
  hoverLift: false,
  pulse: false
})

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

const buttonClass = computed(() => {
  return [
    'btn',
    `btn-${props.type}`,
    `btn-${props.size}`,
    {
      'btn-block': props.block,
      'btn-loading': props.loading,
      'btn-disabled': props.disabled,
      'hover-lift': props.hoverLift,
      'animate-pulse': props.pulse
    }
  ]
})

const handleClick = (e: MouseEvent) => {
  if (!props.disabled && !props.loading) {
    emit('click', e)
  }
}
</script>

<template>
  <button
    :class="buttonClass"
    :disabled="disabled || loading"
    @click="handleClick"
  >
    <span v-if="loading" class="btn-spinner"></span>
    <slot />
  </button>
</template>

<style scoped>
/* ═══════════════════════════════════════════════════════════════
   BUTTON COMPONENT - 按钮组件样式
   ═══════════════════════════════════════════════════════════════ */

.btn {
  /* Layout */
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: var(--space-2);

  /* Typography */
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-medium);
  line-height: 1;
  white-space: nowrap;

  /* Spacing */
  padding: var(--space-2) var(--space-4);

  /* Border & Radius */
  border: 1px solid transparent;
  border-radius: var(--radius-md);

  /* Transition */
  transition: all var(--duration-base) var(--easing-default);

  /* Cursor */
  cursor: pointer;
  user-select: none;

  /* Focus */
  outline: none;
}

.btn:focus-visible {
  outline: 2px solid var(--blue);
  outline-offset: 2px;
}

/* ───────────────────────────────────────────────────────────────
   BUTTON SIZES - 尺寸变体
   ─────────────────────────────────────────────────────────────── */

.btn-sm {
  padding: var(--space-1) var(--space-2);
  font-size: var(--font-size-sm);
  gap: var(--space-1);
}

.btn-md {
  padding: var(--space-2) var(--space-4);
  font-size: var(--font-size-base);
  gap: var(--space-2);
}

.btn-lg {
  padding: var(--space-3) var(--space-6);
  font-size: var(--font-size-md);
  gap: var(--space-2);
}

/* ───────────────────────────────────────────────────────────────
   BUTTON TYPES - 类型变体
   ─────────────────────────────────────────────────────────────── */

.btn-primary {
  background: var(--blue);
  color: white;
  border-color: var(--blue);
}

.btn-primary:hover:not(.btn-disabled):not(.btn-loading) {
  background: var(--blue-hover);
  border-color: var(--blue-hover);
}

.btn-secondary {
  background: var(--s2);
  color: var(--text);
  border-color: var(--border);
}

.btn-secondary:hover:not(.btn-disabled):not(.btn-loading) {
  background: var(--s3);
  border-color: var(--border-hover);
}

.btn-ghost {
  background: transparent;
  color: var(--text);
  border-color: transparent;
}

.btn-ghost:hover:not(.btn-disabled):not(.btn-loading) {
  background: var(--s1);
  border-color: var(--border);
}

.btn-danger {
  background: var(--red);
  color: white;
  border-color: var(--red);
}

.btn-danger:hover:not(.btn-disabled):not(.btn-loading) {
  background: var(--red-hover);
  border-color: var(--red-hover);
}

/* ───────────────────────────────────────────────────────────────
   BUTTON STATES - 状态样式
   ─────────────────────────────────────────────────────────────── */

.btn-disabled,
.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}

.btn-loading {
  position: relative;
  pointer-events: none;
}

.btn-block {
  width: 100%;
  display: flex;
}

/* ───────────────────────────────────────────────────────────────
   BUTTON SPINNER - 加载动画
   ─────────────────────────────────────────────────────────────── */

.btn-spinner {
  display: inline-block;
  width: 12px;
  height: 12px;
  border: 2px solid currentColor;
  border-top-color: transparent;
  border-radius: 50%;
  animation: spin 0.6s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

/* ───────────────────────────────────────────────────────────────
   BUTTON EFFECTS - 交互效果
   ─────────────────────────────────────────────────────────────── */

.hover-lift {
  transition: transform var(--duration-base) var(--easing-default);
}

.hover-lift:hover:not(.btn-disabled):not(.btn-loading) {
  transform: translateY(-2px);
  box-shadow: var(--shadow-lg);
}

.hover-lift:active:not(.btn-disabled):not(.btn-loading) {
  transform: translateY(0);
}
</style>
