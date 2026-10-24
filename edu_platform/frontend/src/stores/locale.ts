import { defineStore } from 'pinia'
import { computed } from 'vue'

import { i18n, SUPPORTED_LOCALES, setLocale, type AppLocale } from '@/i18n'

/**
 * Текущий язык интерфейса (переключатель RU/ҚАЗ в шапке и на странице входа).
 * Читает/пишет напрямую в `i18n.global`, а не через `useI18n()` — стор может
 * создаваться вне контекста компонента (Pinia setup-store), где inject недоступен.
 */
export const useLocaleStore = defineStore('locale', () => {
  const current = computed(() => i18n.global.locale.value as AppLocale)
  const options = SUPPORTED_LOCALES

  function select(value: AppLocale) {
    if (value === current.value) return
    setLocale(value)
  }

  const t = i18n.global.t

  return { current, options, select, t }
})
