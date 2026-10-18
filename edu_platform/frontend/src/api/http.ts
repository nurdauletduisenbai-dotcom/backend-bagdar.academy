import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios'

import type { ApiError, RefreshResponse } from '@/types/api'

// Access-токен живёт только в памяти. Refresh-токен — в HttpOnly cookie,
// которую Django ставит на путь /api/v1/auth/ (JS её не видит).
let accessToken: string | null = null
let onSessionExpired: (() => void) | null = null

export function setAccessToken(token: string | null) {
  accessToken = token
}

export function setSessionExpiredHandler(handler: () => void) {
  onSessionExpired = handler
}

export const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  withCredentials: true,
})

http.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`
  }
  const orgId = localStorage.getItem('org_id')
  if (orgId) {
    config.headers['X-Org-ID'] = orgId
  }
  return config
})

// Один общий запрос на обновление, даже если 401 пришёл сразу на несколько запросов
let refreshPromise: Promise<string> | null = null

export function refreshAccessToken(): Promise<string> {
  refreshPromise ??= axios
    .post<RefreshResponse>(`${http.defaults.baseURL}/auth/refresh/`, {}, { withCredentials: true })
    .then(({ data }) => {
      setAccessToken(data.access_token)
      return data.access_token
    })
    .finally(() => {
      refreshPromise = null
    })
  return refreshPromise
}

type RetriableConfig = InternalAxiosRequestConfig & { _retried?: boolean }

http.interceptors.response.use(
  (response) => response,
  async (error: AxiosError<ApiError>) => {
    const config = error.config as RetriableConfig | undefined
    const isAuthCall = config?.url?.startsWith('/auth/')

    if (error.response?.status === 401 && config && !config._retried && !isAuthCall) {
      config._retried = true
      try {
        await refreshAccessToken()
        return http(config)
      } catch {
        setAccessToken(null)
        onSessionExpired?.()
      }
    }
    return Promise.reject(error)
  },
)

/** Человекочитаемое сообщение из формата ошибок бэкенда */
export function errorMessage(error: unknown): string {
  if (axios.isAxiosError<ApiError>(error)) {
    return error.response?.data?.error?.message ?? error.message
  }
  return 'Неизвестная ошибка'
}
