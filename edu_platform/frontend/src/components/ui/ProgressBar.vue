<script setup lang="ts">
defineProps<{ value: number }>()
</script>

<template>
  <div class="progress" :title="`${value}%`">
    <div class="progress__fill" :style="{ width: `${Math.min(100, Math.max(0, value))}%` }" />
  </div>
</template>

<style scoped>
.progress {
  height: 8px;
  border-radius: 999px;
  background: var(--bg);
  border: 1px solid var(--border);
  overflow: hidden;
}
.progress__fill {
  height: 100%;
  background: var(--primary);
}
</style>
