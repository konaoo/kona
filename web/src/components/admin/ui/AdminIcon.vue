<template>
  <svg
    class="admin-icon"
    :style="{ width: `${size}px`, height: `${size}px` }"
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden="true"
  >
    <path :d="path" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" />
  </svg>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    name?: string
    size?: number
  }>(),
  {
    name: 'dot',
    size: 16,
  },
)

const ICON_PATHS: Record<string, string> = {
  dashboard: 'M4 4h7v7H4zM13 4h7v5h-7zM13 11h7v9h-7zM4 13h7v7H4z',
  users: 'M16 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2M9.5 7a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7ZM20 8a2.5 2.5 0 1 1-2.5 2.5',
  invite: 'M3 8h18v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8ZM3 8l9 6 9-6M8 5h8',
  ops: 'M12 3v3M12 18v3M3 12h3M18 12h3M5.6 5.6l2.1 2.1M16.3 16.3l2.1 2.1M5.6 18.4l2.1-2.1M16.3 7.7l2.1-2.1M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8z',
  api: 'M8 7h8M8 12h8M8 17h8M4 7h.01M4 12h.01M4 17h.01',
  arrow_right: 'M9 6l6 6-6 6',
  dot: 'M12 12h.01',
}

const path = computed(() => ICON_PATHS[props.name] || ICON_PATHS.dot)
</script>

<style scoped>
.admin-icon {
  display: inline-block;
  color: currentColor;
  flex-shrink: 0;
}
</style>
