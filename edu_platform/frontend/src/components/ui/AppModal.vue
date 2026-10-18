<script setup lang="ts">
defineProps<{ title: string; wide?: boolean }>()
const emit = defineEmits<{ close: [] }>()
</script>

<template>
  <div class="modal-backdrop" @click.self="emit('close')">
    <div class="modal card" :class="{ 'modal--wide': wide }" role="dialog" :aria-label="title">
      <header class="modal__header">
        <h2>{{ title }}</h2>
        <button class="btn btn--ghost btn--sm" aria-label="Закрыть" @click="emit('close')">✕</button>
      </header>
      <slot />
    </div>
  </div>
</template>

<style scoped>
.modal-backdrop {
  position: fixed;
  inset: 0;
  background: rgb(0 0 0 / 0.45);
  display: grid;
  place-items: center;
  padding: 16px;
  z-index: 50;
}
.modal {
  width: min(520px, 100%);
  max-height: 90vh;
  overflow: auto;
}
.modal--wide {
  width: min(860px, 100%);
}
.modal__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}
.modal__header h2 {
  margin: 0;
  font-size: 18px;
}
</style>
