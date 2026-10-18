<script setup lang="ts">
import { useToast } from '@/stores/toast'

const toast = useToast()
</script>

<template>
  <div class="toasts" aria-live="polite">
    <div v-for="t in toast.items" :key="t.id" class="toast" :class="`toast--${t.kind}`" @click="toast.dismiss(t.id)">
      {{ t.text }}
    </div>
  </div>
</template>

<style scoped>
.toasts {
  position: fixed;
  right: 16px;
  bottom: 16px;
  display: grid;
  gap: 8px;
  z-index: 100;
  max-width: min(380px, calc(100vw - 32px));
}
.toast {
  padding: 12px 14px;
  border-radius: 8px;
  background: var(--surface);
  border: 1px solid var(--border);
  box-shadow: 0 4px 16px rgb(0 0 0 / 0.12);
  cursor: pointer;
}
.toast--success {
  border-left: 4px solid var(--success);
}
.toast--error {
  border-left: 4px solid var(--danger);
}
.toast--info {
  border-left: 4px solid var(--primary);
}
</style>
