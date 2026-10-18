import { defineStore } from 'pinia'
import { computed, ref } from 'vue'

import { authApi, type LoginPayload } from '@/api/auth'
import { refreshAccessToken, setAccessToken, setSessionExpiredHandler } from '@/api/http'
import { orgsApi } from '@/api/orgs'
import type { AuthUser, OrganizationBrief, Role } from '@/types/api'

const ORG_KEY = 'org_id'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<AuthUser | null>(null)
  const isAuthenticated = computed(() => user.value !== null)
  const roles = computed<Role[]>(() => user.value?.roles ?? [])
  const organizations = computed<OrganizationBrief[]>(() => user.value?.organizations ?? [])
  const currentOrg = computed(() => organizations.value.find((o) => o.id === user.value?.org_id) ?? null)

  const hasRole = (...wanted: Role[]) => wanted.some((r) => roles.value.includes(r))
  const isAdmin = computed(() => hasRole('admin'))
  const isTeacher = computed(() => hasRole('teacher', 'admin'))
  const isStaff = computed(() => hasRole('admin', 'teacher', 'curator'))
  const isStudent = computed(() => hasRole('student'))
  const isParent = computed(() => hasRole('parent'))

  function clear() {
    user.value = null
    setAccessToken(null)
    localStorage.removeItem(ORG_KEY)
  }

  setSessionExpiredHandler(clear)

  function pickOrg(orgs: OrganizationBrief[], preferred: number | null) {
    const stored = Number(localStorage.getItem(ORG_KEY))
    const orgId = orgs.find((o) => o.id === preferred)?.id ?? orgs.find((o) => o.id === stored)?.id ?? orgs[0]?.id ?? null
    if (orgId) localStorage.setItem(ORG_KEY, String(orgId))
    else localStorage.removeItem(ORG_KEY)
    return orgId
  }

  /** Профиль и роли в текущей организации (роли зависят от X-Org-ID) */
  async function loadProfile(preferredOrg: number | null = null) {
    const organizationsList = await orgsApi.my()
    const orgId = pickOrg(organizationsList, preferredOrg)
    const profile = await authApi.me()
    user.value = {
      id: profile.id,
      email: profile.email,
      full_name: `${profile.first_name} ${profile.last_name}`.trim(),
      is_verified: profile.is_verified,
      org_id: orgId,
      roles: profile.roles,
      organizations: organizationsList,
    }
  }

  /** Возвращает true, если нужен код 2FA */
  async function login(payload: LoginPayload): Promise<boolean> {
    const result = await authApi.login(payload)
    if (result.requires_2fa) return true
    setAccessToken(result.access_token)
    await loadProfile(result.user.org_id)
    return false
  }

  async function logout() {
    try {
      await authApi.logout()
    } finally {
      clear()
    }
  }

  async function switchOrg(orgId: number) {
    localStorage.setItem(ORG_KEY, String(orgId))
    await loadProfile(orgId)
  }

  /** При загрузке страницы пробуем восстановить сессию по refresh-cookie */
  async function restore() {
    try {
      await refreshAccessToken()
      await loadProfile()
    } catch {
      clear()
    }
  }

  return {
    user, isAuthenticated, roles, organizations, currentOrg,
    hasRole, isAdmin, isTeacher, isStaff, isStudent, isParent,
    login, logout, restore, switchOrg, loadProfile,
  }
})
