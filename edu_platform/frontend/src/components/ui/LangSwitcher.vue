<script setup lang="ts">
import { useLocaleStore } from '@/stores/locale'

/** Переключатель RU / ҚАЗ. На светлом фоне (шапка) и на тёмном (страница входа) — через класс `dark`. */
defineProps<{ dark?: boolean }>()
const locale = useLocaleStore()

const shortLabel: Record<string, string> = { ru: 'RU', kk: 'ҚАЗ' }
</script>

<template>
  <div class="lang-switcher" :class="{ 'lang-switcher--dark': dark }" role="group" :aria-label="locale.t('lang.switchTo')">
    <button
      v-for="code in locale.options"
      :key="code"
      type="button"
      class="lang-switcher__btn"
      :class="{ active: locale.current === code }"
      :aria-pressed="locale.current === code"
      @click="locale.select(code)"
    >
      {{ shortLabel[code] }}
    </button>
  </div>
</template>

<style scoped>
.lang-switcher {
  display: inline-flex;
  gap: 2px;
  padding: 2px;
  border-radius: var(--radius-full);
  border: 1px solid var(--border-default);
  background: var(--surface-subtle);
}
.lang-switcher__btn {
  padding: 4px 10px;
  border: 0;
  border-radius: var(--radius-full);
  background: transparent;
  color: var(--text-secondary);
  font: 600 var(--fs-caption) / 1 var(--font-sans);
  letter-spacing: 0.3px;
  cursor: pointer;
}
.lang-switcher__btn.active {
  background: var(--surface-card);
  color: var(--text-strong);
  box-shadow: var(--shadow-1);
}
.lang-switcher--dark {
  border-color: rgba(255, 255, 255, 0.18);
  background: rgba(255, 255, 255, 0.06);
}
.lang-switcher--dark .lang-switcher__btn {
  color: var(--text-on-dark-muted);
}
.lang-switcher--dark .lang-switcher__btn.active {
  background: rgba(255, 255, 255, 0.14);
  color: var(--text-on-dark);
  box-shadow: none;
}
</style>
