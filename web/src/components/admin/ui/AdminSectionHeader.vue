<template>
  <div class="admin-section-header">
    <div class="copy">
      <h3 class="title">{{ title }}</h3>
      <p v-if="subtitle" class="subtitle">{{ subtitle }}</p>
    </div>
    <div class="actions">
      <slot name="actions" />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title: string
  subtitle?: string
}>()
</script>

<style scoped>
.admin-section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.copy {
  min-width: 0;
}

.title {
  margin: 0;
  color: #1f3f58;
  font-size: 20px;
  font-weight: 800;
}

.subtitle {
  margin: 6px 0 0;
  color: #55708f;
  font-size: 13px;
}

.actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}
</style>
