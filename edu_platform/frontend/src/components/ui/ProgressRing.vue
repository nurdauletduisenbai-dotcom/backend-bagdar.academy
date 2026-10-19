<script setup lang="ts">
import { computed } from 'vue'

/** Кольцо прогресса (итог теста, прогресс курса) */
const props = withDefaults(defineProps<{ value: number; size?: number; dark?: boolean; label?: string }>(), { size: 88 })
const stroke = computed(() => Math.max(6, Math.round(props.size / 11)))
const r = computed(() => (props.size - stroke.value) / 2)
const c = computed(() => 2 * Math.PI * r.value)
const offset = computed(() => c.value * (1 - Math.min(100, Math.max(0, props.value)) / 100))
</script>

<template>
  <div class="ring" :style="{ width: `${size}px`, height: `${size}px` }">
    <svg :width="size" :height="size">
      <circle :cx="size / 2" :cy="size / 2" :r="r" fill="none" :stroke-width="stroke"
              :stroke="dark ? 'rgba(255,255,255,0.14)' : 'var(--hairline)'" />
      <circle :cx="size / 2" :cy="size / 2" :r="r" fill="none" :stroke-width="stroke" stroke="var(--green-500)"
              stroke-linecap="round" :stroke-dasharray="c" :stroke-dashoffset="offset"
              :transform="`rotate(-90 ${size / 2} ${size / 2})`" />
    </svg>
    <span class="ring__label" :class="{ 'ring__label--dark': dark }" :style="{ fontSize: `${Math.round(size / 4.2)}px` }">
      {{ label ?? `${Math.round(value)}%` }}
    </span>
  </div>
</template>

<style scoped>
.ring {
  position: relative;
  flex-shrink: 0;
}
.ring__label {
  position: absolute;
  inset: 0;
  display: grid;
  place-items: center;
  font-weight: 500;
  color: var(--text-strong);
}
.ring__label--dark {
  color: var(--text-on-dark);
}
</style>
