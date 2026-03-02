<template>
  <section
    class="admin-card"
    :class="[`variant-${variant}`, { padded, clickable, tight }]"
    @click="onClick"
  >
    <slot />
  </section>
</template>

<script setup lang="ts">
const props = withDefaults(
  defineProps<{
    variant?: 'surface' | 'kpi-purple' | 'kpi-blue' | 'kpi-green' | 'plain'
    padded?: boolean
    clickable?: boolean
    tight?: boolean
  }>(),
  {
    variant: 'surface',
    padded: true,
    clickable: false,
    tight: false,
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
  border: 1px solid #dfe6ea;
  border-radius: 18px;
  background: #fff;
  box-shadow: 0 10px 30px rgba(31, 37, 43, 0.08);
}

.admin-card.padded {
  padding: 16px;
}

.admin-card.tight {
  padding: 12px;
}

.admin-card.variant-surface {
  background: #fff;
}

.admin-card.variant-plain {
  border-color: transparent;
  box-shadow: none;
  background: transparent;
}

.admin-card.variant-kpi-purple {
  border-color: #d6cbf9;
  background: linear-gradient(140deg, #b8abeb, #c3b7f2);
}

.admin-card.variant-kpi-blue {
  border-color: #bdd3f8;
  background: linear-gradient(140deg, #9fc0ef, #aed0f7);
}

.admin-card.variant-kpi-green {
  border-color: #bde6d3;
  background: linear-gradient(140deg, #8fd9b4, #9fe2bf);
}

.admin-card.clickable {
  cursor: pointer;
  transition: transform 0.16s ease, box-shadow 0.16s ease;
}

.admin-card.clickable:hover {
  transform: translateY(-1px);
  box-shadow: 0 14px 34px rgba(31, 37, 43, 0.1);
}
</style>
