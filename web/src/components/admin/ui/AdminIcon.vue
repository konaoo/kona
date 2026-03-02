<template>
  <svg
    class="admin-icon"
    :style="{ width: `${size}px`, height: `${size}px` }"
    viewBox="0 0 24 24"
    fill="none"
    xmlns="http://www.w3.org/2000/svg"
    aria-hidden="true"
  >
    <template v-for="(segment, idx) in segments" :key="`${name}-${idx}`">
      <path
        :d="segment"
        stroke="currentColor"
        stroke-width="1.8"
        stroke-linecap="round"
        stroke-linejoin="round"
      />
    </template>
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

const ICON_PATHS: Record<string, string[]> = {
  dashboard: ['M4 4h7v7H4z', 'M13 4h7v5h-7z', 'M13 11h7v9h-7z', 'M4 13h7v7H4z'],
  users: ['M16 21v-2a4 4 0 0 0-4-4H7a4 4 0 0 0-4 4v2', 'M9.5 7a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7z', 'M20 8a2.5 2.5 0 1 1-2.5 2.5'],
  invite: ['M3 8h18v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8z', 'M3 8l9 6 9-6', 'M8 5h8'],
  ops: ['M12 3v3', 'M12 18v3', 'M3 12h3', 'M18 12h3', 'M5.6 5.6l2.1 2.1', 'M16.3 16.3l2.1 2.1', 'M5.6 18.4l2.1-2.1', 'M16.3 7.7l2.1-2.1', 'M12 16a4 4 0 1 0 0-8 4 4 0 0 0 0 8z'],
  api: ['M8 7h8', 'M8 12h8', 'M8 17h8', 'M4 7h.01', 'M4 12h.01', 'M4 17h.01'],
  bell: ['M18 8a6 6 0 1 0-12 0c0 7-3 7-3 7h18s-3 0-3-7', 'M13.7 19a2 2 0 0 1-3.4 0'],
  message: ['M21 15a2 2 0 0 1-2 2H8l-5 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z'],
  dot: ['M12 12h.01'],
}

const segments = computed(() => ICON_PATHS[props.name] || ICON_PATHS.dot)
</script>

<style scoped>
.admin-icon {
  display: inline-block;
  color: currentColor;
  flex-shrink: 0;
}
</style>
