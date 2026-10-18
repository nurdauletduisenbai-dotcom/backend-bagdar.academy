import type { Announcement, AppNotification, Paginated } from '@/types/api'

import { http } from './http'

const data = <T>(p: Promise<{ data: T }>) => p.then((r) => r.data)

export const notificationsApi = {
  list: (params: { is_read?: boolean; page?: number } = {}) =>
    data(http.get<Paginated<AppNotification>>('/notifications/', { params })),
  unreadCount: () => data(http.get<{ unread: number }>('/notifications/unread-count/')),
  read: (id: number) => data(http.post<AppNotification>(`/notifications/${id}/read/`, {})),
  readAll: () => http.post('/notifications/read-all/', {}),
  remove: (id: number) => http.delete(`/notifications/${id}/`),
  preferences: () => data(http.get<{ email_enabled: boolean; in_app_enabled: boolean }>('/notifications/preferences/')),
  updatePreferences: (payload: { email_enabled?: boolean; in_app_enabled?: boolean }) =>
    data(http.patch('/notifications/preferences/', payload)),
}

export const announcementsApi = {
  list: (params: { course?: number; page?: number } = {}) =>
    data(http.get<Paginated<Announcement>>('/announcements/', { params })),
  create: (payload: { title: string; content: string; course?: number | null; notify?: boolean }) =>
    data(http.post<Announcement>('/announcements/', payload)),
  remove: (id: number) => http.delete(`/announcements/${id}/`),
}
