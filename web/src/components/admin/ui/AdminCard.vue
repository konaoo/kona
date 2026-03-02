<template>
  <section class="admin-card" :class="[`tone-${tone}`, { padded, clickable }]" @click="onClick">
    <slot />
  </section>
</template>

<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    tone?: 'default' | 'soft'
    padded?: boolean
    clickable?: boolean
  }>(),
  {
    tone: 'default',
    padded: true,
    clickable: false,
  },
)

const emit = defineEmits<{
  (e: 'click', event: MouseEvent): void
}>()

function onClick(event: MouseEvent) {
  if (!props.clickable) return
  emit('click', event)
}
</script>

<style scoped>
.admin-card {
  border: 1px solid #d7e1ee;
  border-radius: 14px;
  background: #fff;
  box-shadow: 0 12px 36px rgba(16, 36, 62, 0.08);
}

.admin-card.padded {
  padding: 16px;
}

.admin-card.tone-soft {
  background: linear-gradient(180deg, #ffffff, #f8fbff);
}

.admin-card.clickable {
  cursor: pointer;
  transition: transform 0.16s ease, box-shadow 0.16s ease;
}

.admin-card.clickable:hover {
  transform: translateY(-1px);
  box-shadow: 0 16px 32px rgba(16, 36, 62, 0.12);
}
</style>
