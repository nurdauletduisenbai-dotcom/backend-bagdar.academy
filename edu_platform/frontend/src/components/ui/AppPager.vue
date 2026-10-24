<script setup lang="ts">
import AppIcon from './AppIcon.vue'

const props = defineProps<{ page: number; totalPages: number }>()
const emit = defineEmits<{ change: [page: number] }>()
</script>

<template>
  <nav v-if="props.totalPages > 1" class="pager">
    <button class="icon-btn" :disabled="page <= 1" aria-label="Назад" @click="emit('change', page - 1)">
      <AppIcon name="chevron-left" />
    </button>
    <span class="muted small">{{ page }} из {{ totalPages }}</span>
    <button class="icon-btn" :disabled="page >= totalPages" aria-label="Вперёд" @click="emit('change', page + 1)">
      <AppIcon name="chevron-right" />
    </button>
  </nav>
</template>

<style scoped>
.pager {
  display: flex;
  gap: var(--space-sm);
  align-items: center;
  justify-content: center;
  margin-top: var(--space-xl);
}
.icon-btn:disabled {
  opacity: 0.4;
  cursor: default;
}
</style>
