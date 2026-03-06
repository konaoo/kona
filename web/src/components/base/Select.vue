<script setup lang="ts">
/**
 * Select - 选择器组件
 * 下拉选择输入框
 */

import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'

export interface SelectOption {
  /** 选项值 */
  value: string | number
  /** 显示文本 */
  label: string
  /** 是否禁用 */
  disabled?: boolean
  /** 图标 */
  icon?: string
}

export interface SelectProps {
  /** 选项列表 */
  options: SelectOption[]
  /** 当前值（v-model） */
  modelValue?: string | number
  /** 占位符 */
  placeholder?: string
  /** 选择器尺寸 */
  size?: 'sm' | 'md' | 'lg'
  /** 是否禁用 */
  disabled?: boolean
  /** 是否可清除 */
  clearable?: boolean
  /** 是否可搜索 */
  filterable?: boolean
  /** 搜索关键词 */
  filterText?: string
  /** 是否全屏显示（移动端） */
  fullscreen?: boolean
}

const props = withDefaults(defineProps<SelectProps>(), {
  placeholder: '请选择',
  size: 'md',
  disabled: false,
  clearable: false,
  filterable: false,
  filterText: '',
  fullscreen: false
})

const emit = defineEmits<{
  'update:modelValue': [value: string | number]
  'update:filterText': [text: string]
  change: [value: string | number]
  focus: [event: FocusEvent]
  blur: [event: FocusEvent]
  clear: []
}>()

const selectRef = ref<HTMLElement>()
const dropdownRef = ref<HTMLElement>()
const isFocused = ref(false)
const showDropdown = ref(false)
const localFilterText = ref(props.filterText)

const selectClass = computed(() => {
  return [
    'select',
    `select-${props.size}`,
    {
      'select-disabled': props.disabled,
      'select-focused': isFocused.value,
      'select-open': showDropdown.value
    }
  ]
})

const currentLabel = computed(() => {
  const option = props.options.find(opt => opt.value === props.modelValue)
  return option?.label || ''
})

const currentIcon = computed(() => {
  const option = props.options.find(opt => opt.value === props.modelValue)
  return option?.icon || ''
})

const filteredOptions = computed(() => {
  if (!props.filterable || !localFilterText.value) {
    return props.options
  }

  const text = localFilterText.value.toLowerCase()
  return props.options.filter(opt =>
    opt.label.toLowerCase().includes(text)
  )
})

const showClear = computed(() => {
  return props.clearable && !props.disabled && props.modelValue !== undefined
})

const handleFocus = (e: FocusEvent) => {
  isFocused.value = true
  emit('focus', e)
}

const handleBlur = (e: FocusEvent) => {
  isFocused.value = false
  emit('blur', e)
}

const toggleDropdown = async () => {
  if (props.disabled) return

  showDropdown.value = !showDropdown.value

  if (showDropdown.value) {
    await nextTick()
    document.addEventListener('click', handleClickOutside)
  } else {
    document.removeEventListener('click', handleClickOutside)
  }
}

const handleClickOutside = (e: MouseEvent) => {
  if (
    selectRef.value &&
    !selectRef.value.contains(e.target as Node) &&
    dropdownRef.value &&
    !dropdownRef.value.contains(e.target as Node)
  ) {
    showDropdown.value = false
    document.removeEventListener('click', handleClickOutside)
  }
}

const handleSelect = (option: SelectOption) => {
  if (option.disabled) return

  emit('update:modelValue', option.value)
  emit('change', option.value)
  showDropdown.value = false
  localFilterText.value = ''
}

const handleClear = (e: MouseEvent) => {
  e.stopPropagation()
  emit('update:modelValue', undefined as unknown as string | number)
  emit('clear')
}

const handleFilterInput = (e: Event) => {
  const text = (e.target as HTMLInputElement).value
  localFilterText.value = text
  emit('update:filterText', text)
}

// 键盘导航
const handleKeydown = (e: KeyboardEvent) => {
  if (e.key === 'Enter' || e.key === ' ') {
    e.preventDefault()
    toggleDropdown()
  } else if (e.key === 'Escape' && showDropdown.value) {
    e.preventDefault()
    showDropdown.value = false
  }
}

// 清理事件监听
onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})

watch(() => showDropdown.value, (newVal) => {
  if (!newVal) {
    document.removeEventListener('click', handleClickOutside)
  }
})
</script>

<template>
  <div
    ref="selectRef"
    :class="selectClass"
    @click="toggleDropdown"
    @focus="handleFocus"
    @blur="handleBlur"
    tabindex="0"
    @keydown="handleKeydown"
  >
    <div class="select-value">
      <span v-if="currentIcon" class="select-icon">{{ currentIcon }}</span>
      <span v-if="currentLabel" class="select-label">{{ currentLabel }}</span>
      <span v-else class="select-placeholder">{{ placeholder }}</span>
    </div>

    <div class="select-actions">
      <span v-if="showClear" class="select-clear" @click="handleClear">×</span>
      <span class="select-arrow">▼</span>
    </div>

    <teleport to="body">
      <transition name="select-dropdown">
        <div
          v-if="showDropdown"
          ref="dropdownRef"
          :class="['select-dropdown', `select-dropdown-${size}`, { 'select-dropdown-fullscreen': fullscreen }]"
        >
          <div v-if="filterable" class="select-filter" @click.stop>
            <input
              v-model="localFilterText"
              type="text"
              class="select-filter-input"
              placeholder="搜索..."
              @input="handleFilterInput"
            />
          </div>

          <div class="select-options">
            <div
              v-for="option in filteredOptions"
              :key="option.value"
              :class="[
                'select-option',
                {
                  'select-option-selected': option.value === modelValue,
                  'select-option-disabled': option.disabled
                }
              ]"
              @click="handleSelect(option)"
            >
              <span v-if="option.icon" class="select-option-icon">{{ option.icon }}</span>
              <span class="select-option-label">{{ option.label }}</span>
              <span v-if="option.value === modelValue" class="select-option-check">✓</span>
            </div>

            <div v-if="filteredOptions.length === 0" class="select-empty">
              无匹配项
            </div>
          </div>
        </div>
      </transition>
    </teleport>
  </div>
</template>

<style scoped>
/* ═══════════════════════════════════════════════════════════════
   SELECT COMPONENT - 选择器样式
   ═══════════════════════════════════════════════════════════════ */

.select {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: var(--space-2) var(--space-3);
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  cursor: pointer;
  user-select: none;
  transition: all var(--duration-base) var(--easing-default);
}

.select:hover:not(.select-disabled) {
  border-color: var(--border-hover);
}

.select-focused {
  border-color: var(--blue);
  box-shadow: 0 0 0 2px rgba(91, 141, 239, 0.1);
}

.select-open {
  border-color: var(--blue);
}

.select-disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background: var(--s1);
}

/* ───────────────────────────────────────────────────────────────
   SELECT VALUE - 值显示
   ─────────────────────────────────────────────────────────────── */

.select-value {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: var(--space-2);
}

.select-icon {
  font-size: var(--font-size-md);
  line-height: 1;
}

.select-label {
  font-size: var(--font-size-base);
  color: var(--text);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.select-placeholder {
  font-size: var(--font-size-base);
  color: var(--muted);
}

/* ───────────────────────────────────────────────────────────────
   SELECT ACTIONS - 操作按钮
   ─────────────────────────────────────────────────────────────── */

.select-actions {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  flex-shrink: 0;
}

.select-clear {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 16px;
  height: 16px;
  font-size: 16px;
  line-height: 1;
  color: var(--muted);
  border-radius: var(--radius-sm);
  transition: all var(--duration-base) var(--easing-default);
}

.select-clear:hover {
  color: var(--text);
  background: var(--border);
}

.select-arrow {
  font-size: 10px;
  color: var(--muted);
  transition: transform var(--duration-base) var(--easing-default);
}

.select-open .select-arrow {
  transform: rotate(180deg);
}

/* ───────────────────────────────────────────────────────────────
   SIZE VARIANTS - 尺寸变体
   ─────────────────────────────────────────────────────────────── */

.select-sm {
  padding: var(--space-1) var(--space-2);
}

.select-sm .select-label,
.select-sm .select-placeholder {
  font-size: var(--font-size-sm);
}

.select-lg {
  padding: var(--space-3) var(--space-4);
}

.select-lg .select-label,
.select-lg .select-placeholder {
  font-size: var(--font-size-md);
}

/* ───────────────────────────────────────────────────────────────
   DROPDOWN - 下拉菜单
   ─────────────────────────────────────────────────────────────── */

.select-dropdown {
  position: absolute;
  z-index: 1000;
  background: var(--s2);
  border: 1px solid var(--border);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-xl);
  min-width: 200px;
  max-width: 300px;
  max-height: 300px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.select-dropdown-fullscreen {
  position: fixed;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  min-width: 90vw;
  max-width: 90vw;
  max-height: 70vh;
}

/* ───────────────────────────────────────────────────────────────
   FILTER - 搜索框
   ─────────────────────────────────────────────────────────────── */

.select-filter {
  padding: var(--space-3);
  border-bottom: 1px solid var(--border);
}

.select-filter-input {
  width: 100%;
  padding: var(--space-2) var(--space-3);
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: var(--radius-md);
  font-size: var(--font-size-base);
  color: var(--text);
  outline: none;
}

.select-filter-input:focus {
  border-color: var(--blue);
}

/* ───────────────────────────────────────────────────────────────
   OPTIONS - 选项列表
   ─────────────────────────────────────────────────────────────── */

.select-options {
  flex: 1;
  overflow: auto;
  padding: var(--space-1);
}

.select-option {
  display: flex;
  align-items: center;
  gap: var(--space-2);
  padding: var(--space-2) var(--space-3);
  border-radius: var(--radius-sm);
  cursor: pointer;
  transition: all var(--duration-base) var(--easing-default);
  user-select: none;
}

.select-option:hover:not(.select-option-disabled) {
  background: var(--s3);
}

.select-option-selected {
  background: rgba(91, 141, 239, 0.15);
  color: var(--blue);
}

.select-option-disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.select-option-icon {
  font-size: var(--font-size-sm);
}

.select-option-label {
  flex: 1;
  font-size: var(--font-size-sm);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.select-option-check {
  font-size: var(--font-size-sm);
  color: var(--blue);
}

.select-empty {
  padding: var(--space-6);
  text-align: center;
  color: var(--muted);
  font-size: var(--font-size-sm);
}

/* ───────────────────────────────────────────────────────────────
   TRANSITIONS - 过渡动画
   ─────────────────────────────────────────────────────────────── */

.select-dropdown-enter-active,
.select-dropdown-leave-active {
  transition: all 0.2s ease;
}

.select-dropdown-enter-from,
.select-dropdown-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
</style>
