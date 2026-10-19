<script setup lang="ts">
defineProps<{ title: string; subtitle?: string; eyebrow?: string }>()
</script>

<template>
  <div class="page-header">
    <div class="page-header__main">
      <slot name="before" />
      <div v-if="eyebrow" class="eyebrow">{{ eyebrow }}</div>
      <h1>{{ title }}</h1>
      <p v-if="subtitle" class="muted">{{ subtitle }}</p>
    </div>
    <div class="page-header__actions"><slot /></div>
  </div>
</template>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  gap: var(--space-md);
  flex-wrap: wrap;
  margin-bottom: var(--space-xl);
}
.page-header__main {
  display: grid;
  gap: 6px;
}
.page-header p {
  margin: 0;
}
.page-header__actions {
  display: flex;
  gap: var(--space-xs);
  flex-wrap: wrap;
  align-items: center;
}
:slotted(.back) {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: var(--fs-body-sm);
  color: var(--text-tertiary);
}
</style>
