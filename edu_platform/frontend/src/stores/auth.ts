import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { authApi, type LoginPayload } from '@/api/auth'
import { orgsApi } from '@/api/orgs'
import { refreshAccessToken, setAccessToken, setSessionExpiredHandler } from '@/api/http'
import type { AuthUser } from '@/types/api'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<AuthUser | null>(null)
  const isAuthenticated = computed(() => user.value !== null)

  function clear() {
    user.value = null
    setAccessToken(null)
    localStorage.removeItem('org_id')
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
    if (result.user.org_id) {
      localStorage.setItem('org_id', String(result.user.org_id))
    }
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
      const [profile, organizations] = await Promise.all([authApi.me(), orgsApi.my()])
      // Сохранённая организация действительна, только если пользователь в ней ещё состоит
      const stored = Number(localStorage.getItem('org_id'))
      const orgId = organizations.find((o) => o.id === stored)?.id ?? organizations[0]?.id ?? null
      if (orgId) {
        localStorage.setItem('org_id', String(orgId))
      } else {
        localStorage.removeItem('org_id')
      }
      user.value = {
        id: profile.id,
        email: profile.email,
        full_name: `${profile.first_name} ${profile.last_name}`.trim(),
        is_verified: profile.is_verified,
        org_id: orgId,
        roles: profile.roles,
        organizations,
      }
    } catch {
      clear()
    }
  }

  return { user, isAuthenticated, login, logout, restore }
})
