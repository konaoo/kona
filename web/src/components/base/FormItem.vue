<script setup lang="ts">
/**
 * FormItem - 表单项组件
 * 表单字段的包装器
 */

import { computed } from 'vue'

export interface FormItemProps {
  /** 标签文本 */
  label?: string
  /** 字段名称 */
  prop?: string
  /** 是否必填 */
  required?: boolean
  /** 错误提示 */
  error?: string
  /** 帮助文本 */
  help?: string
  /** 标签宽度 */
  labelWidth?: string | number
  /** 标签对齐方式 */
  labelAlign?: 'left' | 'right' | 'top'
  /** 是否显示冒号 */
  showColon?: boolean
  /** 表单项尺寸 */
  size?: 'sm' | 'md' | 'lg'
}

const props = withDefaults(defineProps<FormItemProps>(), {
  required: false,
  labelAlign: 'right',
  showColon: true,
  size: 'md'
})

const itemClass = computed(() => {
  return [
    'form-item',
    `form-item-${props.size}`,
    `form-item-${props.labelAlign}`,
    {
      'form-item-error': props.error
    }
  ]
})

const labelStyle = computed(() => {
  if (props.labelAlign === 'top') {
    return {}
  }

  const width = typeof props.labelWidth === 'number' ? `${props.labelWidth}px` : props.labelWidth
  return { width }
})
</script>

<template>
  <div :class="itemClass">
    <div v-if="label" class="form-item-label" :style="labelStyle">
      <span v-if="required" class="form-item-required">*</span>
      <span class="form-item-label-text">{{ label }}</span>
      <span v-if="showColon && labelAlign !== 'top'" class="form-item-colon">:</span>
    </div>

    <div class="form-item-content">
      <slot />
      <div v-if="error" class="form-item-error">
        {{ error }}
      </div>
      <div v-else-if="help" class="form-item-help">
        {{ help }}
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ═══════════════════════════════════════════════════════════════
   FORM ITEM - 表单项样式
   ═══════════════════════════════════════════════════════════════ */

.form-item {
  display: flex;
  margin-bottom: var(--space-4);
}

/* ───────────────────────────────────────────────────────────────
   LABEL - 标签
   ─────────────────────────────────────────────────────────────── */

.form-item-label {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  font-size: var(--font-size-base);
  color: var(--text);
  line-height: 1.6;
}

.form-item-required {
  color: var(--red);
  margin-right: 4px;
}

.form-item-colon {
  margin-left: 4px;
}

/* ───────────────────────────────────────────────────────────────
   CONTENT - 内容区
   ─────────────────────────────────────────────────────────────── */

.form-item-content {
  flex: 1;
  min-width: 0;
}

/* ───────────────────────────────────────────────────────────────
   ALIGNMENT VARIANTS - 对齐方式
   ─────────────────────────────────────────────────────────────── */

.form-item-left {
  align-items: flex-start;
}

.form-item-left .form-item-label {
  text-align: left;
  padding-right: var(--space-3);
  padding-top: var(--space-2);
}

.form-item-right {
  align-items: flex-start;
}

.form-item-right .form-item-label {
  text-align: right;
  padding-right: var(--space-3);
  padding-top: var(--space-2);
}

.form-item-top {
  flex-direction: column;
}

.form-item-top .form-item-label {
  text-align: left;
  margin-bottom: var(--space-2);
}

/* ───────────────────────────────────────────────────────────────
   SIZE VARIANTS - 尺寸变体
   ─────────────────────────────────────────────────────────────── */

.form-item-sm .form-item-label {
  font-size: var(--font-size-sm);
}

.form-item-md .form-item-label {
  font-size: var(--font-size-base);
}

.form-item-lg .form-item-label {
  font-size: var(--font-size-md);
}

/* ───────────────────────────────────────────────────────────────
   ERROR & HELP - 错误和帮助信息
   ─────────────────────────────────────────────────────────────── */

.form-item-error {
  margin-top: var(--space-1);
  font-size: var(--font-size-xs);
  color: var(--red);
  line-height: 1.4;
}

.form-item-help {
  margin-top: var(--space-1);
  font-size: var(--font-size-xs);
  color: var(--muted);
  line-height: 1.4;
}

/* ───────────────────────────────────────────────────────────────
   ERROR STATE - 错误状态
   ─────────────────────────────────────────────────────────────── */

.form-item-error :deep(.input),
.form-item-error :deep(.select),
.form-item-error :deep(textarea) {
  border-color: var(--red);
}

.form-item-error :deep(.input:focus),
.form-item-error :deep(.select:focus),
.form-item-error :deep(textarea:focus) {
  box-shadow: 0 0 0 2px rgba(240, 90, 85, 0.1);
}
</style>
