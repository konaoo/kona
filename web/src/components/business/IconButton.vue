<script setup lang="ts">
/**
 * IconButton - 图标按钮组件
 * 用于只显示图标的按钮操作
 */

import { computed } from 'vue'

export interface IconButtonProps {
  /** 图标（emoji或字符） */
  icon: string
  /** 提示文字 */
  tooltip?: string
  /** 按钮类型 */
  type?: 'primary' | 'secondary' | 'ghost' | 'danger'
  /** 按钮尺寸 */
  size?: 'sm' | 'md' | 'lg'
  /** 是否禁用 */
  disabled?: boolean
  /** 是否加载中 */
  loading?: boolean
  /** 是否圆形 */
  circle?: boolean
  /** 悬停提升效果 */
  hoverLift?: boolean
}

const props = withDefaults(defineProps<IconButtonProps>(), {
  type: 'ghost',
  size: 'md',
  disabled: false,
  loading: false,
  circle: true,
  hoverLift: true
})

const emit = defineEmits<{
  click: [event: MouseEvent]
}>()

const buttonClass = computed(() => {
  return [
    'icon-button',
    `icon-button-${props.type}`,
    `icon-button-${props.size}`,
    {
      'icon-button-circle': props.circle,
      'icon-button-loading': props.loading,
      'icon-button-disabled': props.disabled,
      'hover-lift': props.hoverLift
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
    :title="tooltip"
    @click="handleClick"
  >
    <span v-if="loading" class="icon-button-spinner"></span>
    <span v-else class="icon-button-icon">{{ icon }}</span>
  </button>
</template>

<style scoped>
/* ═══════════════════════════════════════════════════════════════
   ICON BUTTON - 图标按钮样式
   ═══════════════════════════════════════════════════════════════ */

.icon-button {
  /* Layout */
  display: inline-flex;
  align-items: center;
  justify-content: center;

  /* Size */
  width: var(--space-10);
  height: var(--space-10);

  /* Border & Radius */
  border: 1px solid transparent;
  border-radius: var(--radius-md);

  /* Background */
  background: transparent;

  /* Transition */
  transition: all var(--duration-base) var(--easing-default);

  /* Cursor */
  cursor: pointer;
  user-select: none;

  /* Focus */
  outline: none;
}

.icon-button:focus-visible {
  outline: 2px solid var(--blue);
  outline-offset: 2px;
}

/* ───────────────────────────────────────────────────────────────
   SIZE VARIANTS - 尺寸变体
   ─────────────────────────────────────────────────────────────── */

.icon-button-sm {
  width: var(--space-7);
  height: var(--space-7);
}

.icon-button-sm .icon-button-icon {
  font-size: var(--font-size-sm);
}

.icon-button-md {
  width: var(--space-10);
  height: var(--space-10);
}

.icon-button-md .icon-button-icon {
  font-size: var(--font-size-base);
}

.icon-button-lg {
  width: var(--space-12);
  height: var(--space-12);
}

.icon-button-lg .icon-button-icon {
  font-size: var(--font-size-md);
}

/* ───────────────────────────────────────────────────────────────
   TYPE VARIANTS - 类型变体
   ─────────────────────────────────────────────────────────────── */

.icon-button-primary {
  background: var(--blue);
  color: white;
  border-color: var(--blue);
}

.icon-button-primary:hover:not(.icon-button-disabled):not(.icon-button-loading) {
  background: var(--blue-hover);
  border-color: var(--blue-hover);
}

.icon-button-secondary {
  background: var(--s2);
  color: var(--text);
  border-color: var(--border);
}

.icon-button-secondary:hover:not(.icon-button-disabled):not(.icon-button-loading) {
  background: var(--s3);
  border-color: var(--border-hover);
}

.icon-button-ghost {
  background: transparent;
  color: var(--text);
  border-color: transparent;
}

.icon-button-ghost:hover:not(.icon-button-disabled):not(.icon-button-loading) {
  background: var(--s1);
  border-color: var(--border);
}

.icon-button-danger {
  background: transparent;
  color: var(--red);
  border-color: transparent;
}

.icon-button-danger:hover:not(.icon-button-disabled):not(.icon-button-loading) {
  background: rgba(240, 90, 85, 0.15);
  border-color: var(--red);
}

/* ───────────────────────────────────────────────────────────────
   SHAPE VARIANTS - 形状变体
   ─────────────────────────────────────────────────────────────── */

.icon-button-circle {
  border-radius: 50%;
}

/* ───────────────────────────────────────────────────────────────
   STATES - 状态
   ─────────────────────────────────────────────────────────────── */

.icon-button-disabled,
.icon-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  pointer-events: none;
}

.icon-button-loading {
  pointer-events: none;
}

.icon-button-icon {
  line-height: 1;
}

.icon-button-spinner {
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
   HOVER LIFT - 悬停提升
   ─────────────────────────────────────────────────────────────── */

.hover-lift {
  transition: transform var(--duration-base) var(--easing-default);
}

.hover-lift:hover:not(.icon-button-disabled):not(.icon-button-loading) {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
}

.hover-lift:active:not(.icon-button-disabled):not(.icon-button-loading) {
  transform: translateY(0);
}
</style>
