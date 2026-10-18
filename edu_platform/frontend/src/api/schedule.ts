import type { Attendance, AttendanceStatus, ClassSession, Paginated } from '@/types/api'

import { http } from './http'

const data = <T>(p: Promise<{ data: T }>) => p.then((r) => r.data)

export const sessionsApi = {
  list: (params: { course?: number; group?: number; date_from?: string; date_to?: string; page?: number } = {}) =>
    data(http.get<Paginated<ClassSession>>('/sessions/', { params })),
  create: (payload: Partial<ClassSession>) => data(http.post<ClassSession>('/sessions/', payload)),
  update: (id: number, payload: Partial<ClassSession>) => data(http.patch<ClassSession>(`/sessions/${id}/`, payload)),
  remove: (id: number) => http.delete(`/sessions/${id}/`),
  attendance: (id: number) => data(http.get<Attendance[]>(`/sessions/${id}/attendance/`)),
  markAttendance: (id: number, records: { student_id: number; status: AttendanceStatus; notes?: string }[]) =>
    data(http.put<Attendance[]>(`/sessions/${id}/attendance/`, { records })),
}

export const attendanceApi = {
  list: (params: { student?: number; page?: number } = {}) =>
    data(http.get<Paginated<Attendance>>('/attendance/', { params })),
}
