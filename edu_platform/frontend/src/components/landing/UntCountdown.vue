<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'

import { UNT_DATE } from '@/config/site'

/** Таймер до ҰБТ/ЕНТ (дата — в config/site.ts). Прошедшая или пустая дата — блок не показывается */
const target = UNT_DATE ? new Date(UNT_DATE).getTime() : NaN
const now = ref(Date.now())
let timer: number | undefined

onMounted(() => (timer = window.setInterval(() => (now.value = Date.now()), 30_000)))
onUnmounted(() => window.clearInterval(timer))

const left = computed(() => {
  const ms = target - now.value
  if (!(ms > 0)) return null
  const min = Math.floor(ms / 60_000)
  return { days: Math.floor(min / 1440), hours: Math.floor((min % 1440) / 60), minutes: min % 60 }
})
const pad = (n: number) => String(n).padStart(2, '0')
</script>

<template>
  <div v-if="left" class="countdown">
    <div>
      <div class="countdown__title">{{ $t('landing.countdownTitle') }}</div>
      <div class="countdown__note">{{ $t('landing.countdownNote') }}</div>
    </div>
    <div class="countdown__units">
      <div v-for="u in (['days', 'hours', 'minutes'] as const)" :key="u" class="countdown__unit">
        <span class="countdown__num">{{ u === 'days' ? left[u] : pad(left[u]) }}</span>
        <span class="countdown__label">{{ $t(`landing.${u}`) }}</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.countdown {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-lg);
  flex-wrap: wrap;
  padding: var(--space-lg) var(--space-xl);
  border-radius: var(--radius-lg);
  background: var(--green-500);
  color: var(--teal-900);
}
.countdown__title {
  font: 600 var(--fs-h5) / 1.2 var(--font-sans);
}
.countdown__note {
  font-size: var(--fs-body-sm);
  opacity: 0.8;
}
.countdown__units {
  display: flex;
  gap: var(--space-sm);
}
.countdown__unit {
  min-width: 64px;
  padding: var(--space-xs) var(--space-sm);
  border-radius: var(--radius-md);
  background: rgba(0, 30, 43, 0.08);
  display: grid;
  justify-items: center;
}
.countdown__num {
  font: 600 var(--fs-h3) / 1.1 var(--font-sans);
  font-variant-numeric: tabular-nums;
}
.countdown__label {
  font-size: var(--fs-micro);
}
</style>
