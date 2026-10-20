import { createI18n } from 'vue-i18n'

import kk from './locales/kk'
import ru from './locales/ru'

export type AppLocale = 'kk' | 'ru'
export const SUPPORTED_LOCALES: AppLocale[] = ['kk', 'ru']
export const DEFAULT_LOCALE: AppLocale = 'kk'
export const LOCALE_STORAGE_KEY = 'edu_locale'

export function isAppLocale(value: unknown): value is AppLocale {
  return typeof value === 'string' && (SUPPORTED_LOCALES as string[]).includes(value)
}

/** Сохранённый выбор пользователя > казахский по умолчанию. Браузер не учитываем — казахский обязателен по умолчанию. */
export function readStoredLocale(): AppLocale {
  try {
    const stored = localStorage.getItem(LOCALE_STORAGE_KEY)
    if (isAppLocale(stored)) return stored
  } catch {
    // localStorage недоступен (приватный режим и т.п.) — используем язык по умолчанию
  }
  return DEFAULT_LOCALE
}

export const i18n = createI18n({
  legacy: false,
  locale: readStoredLocale(),
  fallbackLocale: 'ru',
  messages: { kk, ru },
})

export function setLocale(locale: AppLocale) {
  i18n.global.locale.value = locale
  document.documentElement.lang = locale
  try {
    localStorage.setItem(LOCALE_STORAGE_KEY, locale)
  } catch {
    // игнорируем: язык всё равно применится на текущую сессию
  }
}

// Применяем атрибут <html lang> сразу при инициализации
document.documentElement.lang = i18n.global.locale.value
