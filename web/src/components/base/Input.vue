<script setup lang="ts">
/**
 * Input - 输入框组件
 * 基础表单组件
 */

import { computed, ref } from 'vue'

export interface InputProps {
  /** 输入框类型 */
  type?: 'text' | 'number' | 'password' | 'email' | 'tel' | 'search'
  /** 输入框尺寸 */
  size?: 'sm' | 'md' | 'lg'
  /** 占位符 */
  placeholder?: string
  /** 是否禁用 */
  disabled?: boolean
  /** 是否只读 */
  readonly?: boolean
  /** 最大长度 */
  maxlength?: number
  /** 最小长度 */
  minlength?: number
  /** 是否可清除 */
  clearable?: boolean
  /** 前置图标 */
  prefixIcon?: string
  /** 后置图标 */
  suffixIcon?: string
  /** 错误状态 */
  error?: boolean
  /** 错误提示文字 */
  errorText?: string
  /** 输入框值（v-model） */
  modelValue?: string | number
  /** 数字输入框的最小值 */
  min?: number
  /** 数字输入框的最大值 */
  max?: number
  /** 数字输入框的步长 */
  step?: number
}

const props = withDefaults(defineProps<InputProps>(), {
  type: 'text',
  size: 'md',
  disabled: false,
  readonly: false,
  clearable: false,
  error: false,
  modelValue: ''
})

const emit = defineEmits<{
  'update:modelValue': [value: string | number]
  focus: [event: FocusEvent]
  blur: [event: FocusEvent]
  change: [value: string | number]
  clear: []
  enter: [event: KeyboardEvent]
}>()

const inputRef = ref<HTMLInputElement>()
const isFocused = ref(false)

const inputClass = computed(() => {
  return [
    'input',
    `input-${props.size}`,
    {
      'input-disabled': props.disabled,
      'input-readonly': props.readonly,
      'input-error': props.error,
      'input-focused': isFocused.value,
      'input-has-prefix': props.prefixIcon,
      'input-has-suffix': props.suffixIcon || props.clearable
    }
  ]
})

const showClear = computed(() => {
  return props.clearable && !props.disabled && !props.readonly && props.modelValue
})

const handleInput = (e: Event) => {
  const target = e.target as HTMLInputElement
  const value = props.type === 'number' ? Number(target.value) : target.value
  emit('update:modelValue', value)
}

const handleFocus = (e: FocusEvent) => {
  isFocused.value = true
  emit('focus', e)
}

const handleBlur = (e: FocusEvent) => {
  isFocused.value = false
  emit('blur', e)
  emit('change', props.modelValue)
}

const handleClear = () => {
  emit('update:modelValue', '')
  emit('clear')
  inputRef.value?.focus()
}

const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Enter') {
    emit('enter', e)
  }
}

const focus = () => {
  inputRef.value?.focus()
}

const blur = () => {
  inputRef.value?.blur()
}

defineExpose({
  focus,
  blur
})
</script>

<template>
  <div class="input-wrapper">
    <div class="input-container">
      <span v-if="prefixIcon" class="input-icon input-prefix-icon">
        {{ prefixIcon }}
      </span>

      <input
        ref="inputRef"
        :class="inputClass"
        :type="type"
        :placeholder="placeholder"
        :disabled="disabled"
        :readonly="readonly"
        :maxlength="maxlength"
        :minlength="minlength"
        :min="min"
        :max="max"
        :step="step"
        :value="modelValue"
        @input="handleInput"
        @focus="handleFocus"
        @blur="handleBlur"
        @keydown="handleKeydown"
      />

      <span v-if="showClear" class="input-icon input-clear-icon" @click="handleClear">
        ×
      </span>

      <span v-else-if="suffixIcon" class="input-icon input-suffix-icon">
        {{ suffixIcon }}
      </span>
    </div>

    <div v-if="error && errorText" class="input-error-text">
      {{ errorText }}
    </div>
  </div>
</template>

<style scoped>
/* ═══════════════════════════════════════════════════════════════
   INPUT COMPONENT - 输入框组件样式
   ═══════════════════════════════════════════════════════════════ */

.input-wrapper {
  display: flex;
  flex-direction: column;
  width: 100%;
}

.input-container {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
}

/* ───────────────────────────────────────────────────────────────
   INPUT BASE - 基础样式
   ─────────────────────────────────────────────────────────────── */

.input {
  /* Layout */
  width: 100%;
  display: block;

  /* Typography */
  font-size: var(--font-size-base);
  line-height: 1.5;
  color: var(--text);

  /* Spacing */
  padding: var(--space-2) var(--space-3);

  /* Background & Border */
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);

  /* Transition */
  transition: all var(--duration-base) var(--easing-default);

  /* Placeholder */
  &::placeholder {
    color: var(--muted);
  }

  /* Focus */
  &:focus {
    outline: none;
    border-color: var(--blue);
    box-shadow: 0 0 0 2px rgba(91, 141, 239, 0.1);
  }

  /* Disable */
  &:disabled {
    opacity: 0.5;
    cursor: not-allowed;
    background: var(--s1);
  }

  /* Readonly */
  &.input-readonly {
    background: var(--s1);
    cursor: default;
  }
}

/* ───────────────────────────────────────────────────────────────
   INPUT SIZES - 尺寸变体
   ─────────────────────────────────────────────────────────────── */

.input-sm {
  padding: var(--space-1) var(--space-2);
  font-size: var(--font-size-sm);
}

.input-md {
  padding: var(--space-2) var(--space-3);
  font-size: var(--font-size-base);
}

.input-lg {
  padding: var(--space-3) var(--space-4);
  font-size: var(--font-size-md);
}

/* ───────────────────────────────────────────────────────────────
   INPUT WITH ICONS - 带图标的输入框
   ─────────────────────────────────────────────────────────────── */

.input-has-prefix {
  padding-left: var(--space-8);
}

.input-has-suffix {
  padding-right: var(--space-8);
}

.input-icon {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: var(--font-size-md);
  color: var(--muted);
  pointer-events: none;
}

.input-prefix-icon {
  left: var(--space-2);
}

.input-suffix-icon {
  right: var(--space-2);
}

.input-clear-icon {
  right: var(--space-2);
  cursor: pointer;
  pointer-events: auto;
  font-size: 18px;
  line-height: 1;
  transition: all var(--duration-base) var(--easing-default);
}

.input-clear-icon:hover {
  color: var(--text);
}

/* ───────────────────────────────────────────────────────────────
   INPUT STATES - 状态样式
   ─────────────────────────────────────────────────────────────── */

.input-error {
  border-color: var(--red);
}

.input-error:focus {
  border-color: var(--red);
  box-shadow: 0 0 0 2px rgba(240, 90, 85, 0.1);
}

.input-error-text {
  margin-top: var(--space-1);
  font-size: var(--font-size-xs);
  color: var(--red);
  line-height: 1.4;
}

.input-focused {
  border-color: var(--blue);
}
</style>
