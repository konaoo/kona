<template>
  <div class="admin-table-wrap" :class="{ compact }">
    <table class="table admin-table">
      <slot />
    </table>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    compact?: boolean
  }>(),
  {
    compact: false,
  },
)
</script>

<style scoped>
.admin-table-wrap {
  width: 100%;
  overflow-x: auto;
  border: 1px solid #dfe8f4;
  border-radius: 12px;
}

.admin-table {
  min-width: 100%;
  border-collapse: collapse;
}

.admin-table-wrap.compact :deep(th),
.admin-table-wrap.compact :deep(td) {
  padding: 8px;
  font-size: 12px;
}
</style>
