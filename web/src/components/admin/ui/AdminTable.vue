<template>
  <div class="admin-table-wrap" :class="{ compact, plain }">
    <table class="table admin-table">
      <slot />
    </table>
  </div>
</template>

<script setup lang="ts">
withDefaults(
  defineProps<{
    compact?: boolean
    plain?: boolean
  }>(),
  {
    compact: false,
    plain: false,
  },
)
</script>

<style scoped>
.admin-table-wrap {
  width: 100%;
  overflow-x: auto;
  border: 1px solid #dfe6ea;
  border-radius: 14px;
  background: #fff;
}

.admin-table-wrap.plain {
  border: 0;
  border-radius: 0;
}

.admin-table {
  min-width: 100%;
  border-collapse: collapse;
}

.admin-table :deep(th),
.admin-table :deep(td) {
  border-bottom: 1px solid #edf1f4;
}

.admin-table :deep(th) {
  background: #f7fafb;
  color: #7d8893;
  font-weight: 700;
}

.admin-table :deep(td) {
  color: #25303a;
}

.admin-table :deep(tbody tr:hover) {
  background: #f8fcfd;
}

.admin-table-wrap.compact :deep(th),
.admin-table-wrap.compact :deep(td) {
  padding: 8px;
  font-size: 12px;
}
</style>
