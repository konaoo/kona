<template>
  <div class="admin-section-header" :class="{ tight }">
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
withDefaults(
  defineProps<{
    title: string
    subtitle?: string
    tight?: boolean
  }>(),
  {
    tight: false,
  },
)
</script>

<style scoped>
.admin-section-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 12px;
}

.admin-section-header.tight {
  margin-bottom: 8px;
}

.copy {
  min-width: 0;
}

.title {
  margin: 0;
  color: #1f252b;
  font-size: 22px;
  font-weight: 800;
}

.subtitle {
  margin: 6px 0 0;
  color: #8a939c;
  font-size: 13px;
  font-weight: 600;
}

.actions {
  display: flex;
  gap: 8px;
  align-items: center;
  flex-wrap: wrap;
}
</style>
