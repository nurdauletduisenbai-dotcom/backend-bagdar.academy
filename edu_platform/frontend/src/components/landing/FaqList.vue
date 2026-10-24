<script setup lang="ts">
import AppIcon from '@/components/ui/AppIcon.vue'

/** Частые вопросы: нативные <details> — работают с клавиатуры и скринридером без JS */
const items = [1, 2, 3, 4, 5, 6]
</script>

<template>
  <div class="faq">
    <details v-for="n in items" :key="n" class="faq__item">
      <summary>
        <span>{{ $t(`landing.faq${n}Q`) }}</span>
        <AppIcon name="chevron-down" :size="18" class="faq__chevron" />
      </summary>
      <p>{{ $t(`landing.faq${n}A`) }}</p>
    </details>
  </div>
</template>

<style scoped>
.faq {
  display: grid;
  border-top: 1px solid var(--border-default);
}
.faq__item {
  border-bottom: 1px solid var(--border-default);
}
.faq__item summary {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-lg) 0;
  cursor: pointer;
  list-style: none;
  font: 500 var(--fs-h5) / 1.35 var(--font-sans);
  color: var(--text-strong);
}
.faq__item summary::-webkit-details-marker {
  display: none;
}
.faq__item summary:focus-visible {
  outline: 2px solid var(--border-focus);
  outline-offset: 4px;
  border-radius: var(--radius-sm);
}
.faq__chevron {
  flex-shrink: 0;
  color: var(--text-secondary);
  transition: transform 0.2s;
}
.faq__item[open] .faq__chevron {
  transform: rotate(180deg);
}
.faq__item p {
  margin: 0 0 var(--space-lg);
  max-width: 720px;
  color: var(--text-secondary);
  line-height: 1.6;
}
</style>
