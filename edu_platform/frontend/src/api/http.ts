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

/** Скачать защищённый файл (download_url из API) с токеном и сохранить на диск */
export async function downloadFile(url: string, filename: string) {
  const path = url.replace(/^\/api\/v1/, '')
  const response = await http.get<Blob>(path, { responseType: 'blob' })
  const disposition = String(response.headers['content-disposition'] ?? '')
  const match = /filename\*?=(?:UTF-8'')?"?([^";]+)"?/i.exec(disposition)
  const name = match ? decodeURIComponent(match[1]) : filename
  const link = document.createElement('a')
  link.href = URL.createObjectURL(response.data)
  link.download = name
  link.click()
  URL.revokeObjectURL(link.href)
}

/** Объект -> FormData (для загрузки файлов). Пустые значения пропускаются */
export function toFormData(data: Record<string, unknown>): FormData {
  const form = new FormData()
  for (const [key, value] of Object.entries(data)) {
    if (value === undefined || value === null || value === '') continue
    form.append(key, value instanceof Blob ? value : String(value))
  }
  return form
}
