import type { Assignment, Paginated, Submission } from '@/types/api'

import { http, toFormData } from './http'

const data = <T>(p: Promise<{ data: T }>) => p.then((r) => r.data)

export const assignmentsApi = {
  list: (params: { course?: number; lesson?: number; page?: number } = {}) =>
    data(http.get<Paginated<Assignment>>('/assignments/', { params })),
  get: (id: number) => data(http.get<Assignment>(`/assignments/${id}/`)),
  create: (payload: Partial<Assignment>) => data(http.post<Assignment>('/assignments/', payload)),
  update: (id: number, payload: Partial<Assignment>) => data(http.patch<Assignment>(`/assignments/${id}/`, payload)),
  remove: (id: number) => http.delete(`/assignments/${id}/`),
  submit: (id: number, payload: { text_content?: string; file?: File | null; file_url?: string }) =>
    data(http.post<Submission>(`/assignments/${id}/submit/`, toFormData(payload))),
  submissions: (id: number) => data(http.get<Paginated<Submission>>(`/assignments/${id}/submissions/`)),
}

export const submissionsApi = {
  list: (params: { assignment?: number; student?: number; status?: string; page?: number } = {}) =>
    data(http.get<Paginated<Submission>>('/submissions/', { params })),
  get: (id: number) => data(http.get<Submission>(`/submissions/${id}/`)),
  grade: (id: number, payload: { score: number; feedback?: string; can_resubmit?: boolean }) =>
    data(http.post<Submission>(`/submissions/${id}/grade/`, payload)),
}
