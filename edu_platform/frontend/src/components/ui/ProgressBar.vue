<script setup lang="ts">
defineProps<{ value: number; dark?: boolean }>()
</script>

<template>
  <div class="progress" :class="{ 'progress--dark': dark }" :title="`${value}%`">
    <div class="progress__fill" :style="{ width: `${Math.min(100, Math.max(0, value))}%` }" />
  </div>
</template>

<style scoped>
.progress {
  height: 6px;
  border-radius: var(--radius-full);
  background: var(--hairline-soft);
  overflow: hidden;
  min-width: 60px;
}
.progress--dark {
  background: rgba(255, 255, 255, 0.14);
}
.progress__fill {
  height: 100%;
  border-radius: var(--radius-full);
  background: var(--green-500);
  transition: width var(--dur-base) var(--ease-standard);
}
</style>
