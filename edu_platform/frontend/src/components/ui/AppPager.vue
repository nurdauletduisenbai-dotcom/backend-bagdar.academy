<script setup lang="ts">
const props = defineProps<{ page: number; totalPages: number }>()
const emit = defineEmits<{ change: [page: number] }>()
</script>

<template>
  <nav v-if="props.totalPages > 1" class="pager">
    <button class="btn btn--ghost btn--sm" :disabled="page <= 1" @click="emit('change', page - 1)">← Назад</button>
    <span class="muted">{{ page }} / {{ totalPages }}</span>
    <button class="btn btn--ghost btn--sm" :disabled="page >= totalPages" @click="emit('change', page + 1)">Вперёд →</button>
  </nav>
</template>

<style scoped>
.pager {
  display: flex;
  gap: 12px;
  align-items: center;
  justify-content: center;
  margin-top: 16px;
}
</style>
