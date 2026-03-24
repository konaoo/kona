<template>
  <button
    class="admin-btn"
    :class="[
      `variant-${variant}`,
      `size-${size}`,
      { block, pill, soft, loading }
    ]"
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
    pill?: boolean
    soft?: boolean
    disabled?: boolean
    loading?: boolean
    loadingText?: string
    type?: 'button' | 'submit' | 'reset'
  }>(),
  {
    variant: 'primary',
    size: 'md',
    block: false,
    pill: false,
    soft: false,
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
  border-radius: 12px;
  cursor: pointer;
  font-weight: 700;
  transition: all 0.16s ease;
}

.admin-btn.size-md {
  padding: 9px 13px;
  min-height: 38px;
  font-size: 13px;
}

.admin-btn.size-sm {
  padding: 6px 10px;
  min-height: 32px;
  font-size: 12px;
}

.admin-btn.block {
  width: 100%;
}

.admin-btn.pill {
  border-radius: 999px;
}

.admin-btn.variant-primary {
  color: #fff;
  border-color: #2aa8b4;
  background: linear-gradient(120deg, #1692a0, #25aab6);
}

.admin-btn.variant-secondary {
  color: #2f3b46;
  border-color: #cfd7dd;
  background: #fff;
}

.admin-btn.variant-danger {
  color: #fff;
  border-color: #d54242;
  background: linear-gradient(120deg, #cc3434, #de4b4b);
}

.admin-btn.variant-ghost {
  color: #4f5c69;
  border-color: #d7dee4;
  background: #f8fbfd;
}

.admin-btn.soft.variant-primary {
  color: #1d4953;
  border-color: #c8e8ec;
  background: #eaf8fa;
}

.admin-btn.soft.variant-secondary {
  color: #5a6773;
  border-color: #e3e9ee;
  background: #f5f8fa;
}

.admin-btn:hover:not(:disabled) {
  filter: brightness(1.02);
  transform: translateY(-1px);
}

.admin-btn:disabled {
  opacity: 0.56;
  cursor: not-allowed;
  transform: none;
}
</style>
