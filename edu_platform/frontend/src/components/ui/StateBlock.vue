<script setup lang="ts">
defineProps<{ loading?: boolean; error?: string; empty?: boolean; emptyText?: string }>()
const emit = defineEmits<{ retry: [] }>()
</script>

<template>
  <div v-if="loading" class="state">
    <span class="spinner" aria-hidden="true" /> Загрузка…
  </div>
  <div v-else-if="error" class="alert alert--error">
    {{ error }}
    <button class="btn btn--ghost btn--sm" @click="emit('retry')">Повторить</button>
  </div>
  <div v-else-if="empty" class="state state--empty">{{ emptyText ?? 'Пока ничего нет.' }}</div>
  <slot v-else />
</template>

<style scoped>
.state {
  display: flex;
  align-items: center;
  gap: 10px;
  color: var(--text-tertiary);
  font-size: var(--fs-body-sm);
  padding: var(--space-md) 0;
}
.state--empty {
  justify-content: center;
  padding: var(--space-xl);
  border: 1px dashed var(--border-default);
  border-radius: var(--radius-md);
  background: var(--surface-subtle);
}
.spinner {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 2px solid var(--hairline);
  border-top-color: var(--green-600);
  animation: spin 0.8s linear infinite;
}
@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
