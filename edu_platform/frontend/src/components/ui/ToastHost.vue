<script setup lang="ts">
import { useToast } from '@/stores/toast'

import AppIcon from './AppIcon.vue'

const toast = useToast()
const icon = { success: 'check', error: 'x', info: 'info' } as const
</script>

<template>
  <div class="toasts" aria-live="polite">
    <div v-for="t in toast.items" :key="t.id" class="toast" :class="`toast--${t.kind}`" @click="toast.dismiss(t.id)">
      <span class="toast__icon"><AppIcon :name="icon[t.kind]" :size="14" /></span>
      <span>{{ t.text }}</span>
    </div>
  </div>
</template>

<style scoped>
.toasts {
  position: fixed;
  right: var(--space-md);
  bottom: var(--space-md);
  display: grid;
  gap: var(--space-xs);
  z-index: 100;
  max-width: min(400px, calc(100vw - 32px));
}
.toast {
  display: flex;
  gap: var(--space-sm);
  align-items: flex-start;
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-md);
  background: var(--teal-900);
  color: var(--text-on-dark);
  box-shadow: var(--shadow-3);
  cursor: pointer;
  font-size: var(--fs-body-sm);
}
.toast__icon {
  display: grid;
  place-items: center;
  width: 22px;
  height: 22px;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--green-500);
  color: var(--teal-900);
}
.toast--error .toast__icon {
  background: #ff6b5e;
  color: #fff;
}
.toast--info .toast__icon {
  background: rgba(255, 255, 255, 0.16);
  color: var(--text-on-dark);
}
</style>
