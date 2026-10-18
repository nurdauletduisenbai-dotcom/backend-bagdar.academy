<script setup lang="ts">
defineProps<{ loading?: boolean; error?: string; empty?: boolean; emptyText?: string }>()
const emit = defineEmits<{ retry: [] }>()
</script>

<template>
  <p v-if="loading" class="muted">Загрузка…</p>
  <div v-else-if="error" class="alert alert--error">
    {{ error }}
    <button class="btn btn--ghost btn--sm" @click="emit('retry')">Повторить</button>
  </div>
  <p v-else-if="empty" class="muted">{{ emptyText ?? 'Пока ничего нет.' }}</p>
  <slot v-else />
</template>
