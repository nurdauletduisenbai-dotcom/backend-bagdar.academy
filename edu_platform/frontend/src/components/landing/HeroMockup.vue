<script setup lang="ts">
import AppIcon from '@/components/ui/AppIcon.vue'
import ProgressRing from '@/components/ui/ProgressRing.vue'

/** Иллюстрация интерфейса (экран теста) для героя главной — декоративная, без реальных данных */
const options = ['1/2', '√3/2', '1', '0']
</script>

<template>
  <div class="mock" aria-hidden="true">
    <div class="mock__card">
      <div class="mock__head">
        <span class="mock__subject">{{ $t('landing.mockSubject') }}</span>
        <span class="mock__timer"><AppIcon name="clock" :size="14" /> 24:15</span>
      </div>
      <div class="mock__bar"><span style="width: 30%" /></div>
      <span class="mock__progress">{{ $t('landing.mockProgress') }}</span>
      <p class="mock__question">{{ $t('landing.mockQuestion') }}</p>
      <ul class="mock__options">
        <li v-for="(o, i) in options" :key="o" :class="{ picked: i === 0 }">
          <span class="mock__letter">{{ 'ABCD'[i] }}</span> {{ o }}
          <AppIcon v-if="i === 0" name="check" :size="16" class="mock__ok" />
        </li>
      </ul>
    </div>

    <div class="mock__chip mock__chip--analysis">
      <span class="mock__dot"><AppIcon name="check" :size="12" /></span> {{ $t('landing.mockAnalysis') }}
    </div>
    <div class="mock__chip mock__chip--topic">
      <ProgressRing :value="68" :size="44" />
      <span>
        <strong>{{ $t('landing.mockTopic') }}</strong>
        <small>{{ $t('landing.mockMastery') }}</small>
      </span>
    </div>
  </div>
</template>

<style scoped>
.mock {
  position: relative;
  padding: var(--space-xl) var(--space-xl) var(--space-xxxl);
}
.mock__card {
  background: var(--canvas);
  color: var(--text-strong);
  border-radius: var(--radius-xl);
  padding: var(--space-xl);
  display: grid;
  gap: var(--space-sm);
  box-shadow: 0 24px 48px rgba(0, 0, 0, 0.28);
  transform: rotate(-1.5deg);
}
.mock__head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-sm);
}
.mock__subject {
  font: 600 var(--fs-caption) / 1.2 var(--font-sans);
  color: var(--text-secondary);
}
.mock__timer {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border-radius: var(--radius-full);
  background: var(--surface-soft);
  font: 600 var(--fs-caption) / 1 var(--font-sans);
}
.mock__bar {
  height: 6px;
  border-radius: var(--radius-full);
  background: var(--surface-soft);
  overflow: hidden;
}
.mock__bar span {
  display: block;
  height: 100%;
  background: var(--green-500);
}
.mock__progress {
  font-size: var(--fs-micro);
  color: var(--text-tertiary);
}
.mock__question {
  margin: var(--space-xs) 0;
  font: 500 var(--fs-h5) / 1.35 var(--font-sans);
}
.mock__options {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: var(--space-xs);
}
.mock__options li {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: 10px 12px;
  border: 1px solid var(--border-default);
  border-radius: var(--radius-md);
  font-size: var(--fs-body-sm);
}
.mock__options li.picked {
  border-color: var(--green-dark);
  background: var(--surface-feature);
}
.mock__letter {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--surface-soft);
  font: 600 var(--fs-micro) / 1 var(--font-sans);
}
.picked .mock__letter {
  background: var(--green-500);
  color: var(--teal-900);
}
.mock__ok {
  margin-left: auto;
  color: var(--green-dark);
}
.mock__chip {
  position: absolute;
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  padding: 10px 14px;
  border-radius: var(--radius-lg);
  background: var(--canvas);
  color: var(--text-strong);
  box-shadow: 0 12px 28px rgba(0, 0, 0, 0.25);
  font: 600 var(--fs-caption) / 1.2 var(--font-sans);
}
.mock__chip--analysis {
  top: 0;
  right: 0;
}
.mock__chip--topic {
  bottom: 0;
  left: 0;
}
.mock__chip--topic span {
  display: grid;
}
.mock__chip small {
  font-weight: 400;
  color: var(--text-secondary);
}
.mock__dot {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  background: var(--green-500);
  color: var(--teal-900);
}
</style>
