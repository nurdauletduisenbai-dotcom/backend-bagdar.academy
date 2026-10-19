<script setup lang="ts">
import AppIcon from './AppIcon.vue'

defineProps<{ title: string; wide?: boolean }>()
const emit = defineEmits<{ close: [] }>()
</script>

<template>
  <div class="modal-backdrop" @click.self="emit('close')">
    <div class="modal" :class="{ 'modal--wide': wide }" role="dialog" :aria-label="title">
      <header class="modal__header">
        <h2>{{ title }}</h2>
        <button class="icon-btn" aria-label="Закрыть" @click="emit('close')"><AppIcon name="x" /></button>
      </header>
      <div class="modal__body"><slot /></div>
    </div>
  </div>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgba(0, 30, 43, 0.55);
  display: grid;
  place-items: center;
  padding: var(--space-md);
  z-index: 50;
}
.modal {
  width: min(560px, 100%);
  max-height: 90vh;
  overflow: auto;
  background: var(--surface-card);
  border-radius: var(--radius-xl);
  box-shadow: var(--shadow-4);
}
.modal--wide {
  width: min(880px, 100%);
}
.modal__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--space-lg) var(--space-xl);
  border-bottom: 1px solid var(--border-default);
  position: sticky;
  top: 0;
  background: var(--surface-card);
  z-index: 1;
}
.modal__header h2 {
  margin: 0;
}
.modal__body {
  padding: var(--space-xl);
}
</style>
