<template>
  <button
    class="admin-btn"
    :class="[`variant-${variant}`, `size-${size}`, { block }]"
    :type="type"
    :disabled="disabled || loading"
    @click="onClick"
  >
    <slot>{{ loading ? loadingText : '' }}</slot>
  </button>
</template>

<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
    size?: 'md' | 'sm'
    block?: boolean
    disabled?: boolean
    loading?: boolean
    loadingText?: string
    type?: 'button' | 'submit' | 'reset'
  }>(),
  {
    variant: 'primary',
    size: 'md',
    block: false,
    disabled: false,
    loading: false,
    loadingText: '处理中...',
    type: 'button',
  },
)

const emit = defineEmits<{
  (e: 'click', event: MouseEvent): void
}>()

function onClick(event: MouseEvent) {
  if (props.disabled || props.loading) return
  emit('click', event)
}
</script>

<style scoped>
.admin-btn {
  border: 1px solid transparent;
  border-radius: 10px;
  cursor: pointer;
  font-weight: 700;
  transition: all 0.16s ease;
}

.admin-btn.size-md {
  padding: 8px 12px;
  min-height: 36px;
  font-size: 13px;
}

.admin-btn.size-sm {
  padding: 6px 10px;
  min-height: 30px;
  font-size: 12px;
}

.admin-btn.block {
  width: 100%;
}

.admin-btn.variant-primary {
  color: #fff;
  background: linear-gradient(120deg, #0f5f73, #0a8f98);
}

.admin-btn.variant-secondary {
  color: #1f3f58;
  background: #e8eff7;
  border-color: #c8d6e7;
}

.admin-btn.variant-danger {
  color: #fff;
  background: linear-gradient(120deg, #b42318, #d92d20);
}

.admin-btn.variant-ghost {
  color: #35557d;
  background: #fff;
  border-color: #c8d6e7;
}

.admin-btn:hover:not(:disabled) {
  filter: brightness(1.04);
}

.admin-btn:disabled {
  opacity: 0.56;
  cursor: not-allowed;
}
</style>
