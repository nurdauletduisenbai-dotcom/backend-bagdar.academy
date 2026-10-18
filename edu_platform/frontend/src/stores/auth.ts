import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { authApi, type LoginPayload } from '@/api/auth'
import { refreshAccessToken, setAccessToken, setSessionExpiredHandler } from '@/api/http'
import type { AuthUser } from '@/types/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<AuthUser | null>(null)
  const isAuthenticated = computed(() => user.value !== null)

  function clear() {
    user.value = null
    setAccessToken(null)
  }

  setSessionExpiredHandler(clear)

  /** Возвращает true, если нужен код 2FA */
  async function login(payload: LoginPayload): Promise<boolean> {
    const result = await authApi.login(payload)
    if (result.requires_2fa) {
      return true
    }
    setAccessToken(result.access_token)
    user.value = result.user
    return false
  }

  async function logout() {
    try {
      await authApi.logout()
    } finally {
      clear()
    }
  }

  /** При загрузке страницы пробуем восстановить сессию по refresh-cookie */
  async function restore() {
    try {
      await refreshAccessToken()
      const profile = await authApi.me()
      user.value = {
        id: profile.id,
        email: profile.email,
        full_name: `${profile.first_name} ${profile.last_name}`.trim(),
        is_verified: profile.is_verified,
        roles: profile.roles,
      }
    } catch {
      clear()
    }
  }

  return { user, isAuthenticated, login, logout, restore }
})
