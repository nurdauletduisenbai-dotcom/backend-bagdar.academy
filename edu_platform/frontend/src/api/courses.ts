import type { Course, CourseDetail, Enrollment, Group, GroupStudent, Paginated } from '@/types/api'

import { http } from './http'

const data = <T>(p: Promise<{ data: T }>) => p.then((r) => r.data)

export interface CourseFilters {
  search?: string
  type?: Course['type']
  status?: Course['status']
  subject?: string
  page?: number
}

export type CoursePayload = Partial<Omit<Course, 'id' | 'created_at'>> & { description?: string }

export const coursesApi = {
  list: (params: CourseFilters = {}) => data(http.get<Paginated<Course>>('/courses/', { params })),
  my: () => data(http.get<Paginated<Course>>('/courses/my/')),
  get: (id: number) => data(http.get<CourseDetail>(`/courses/${id}/`)),
  create: (payload: CoursePayload) => data(http.post<Course>('/courses/', payload)),
  update: (id: number, payload: CoursePayload) => data(http.patch<Course>(`/courses/${id}/`, payload)),
  remove: (id: number) => http.delete(`/courses/${id}/`),
  enrollments: (id: number) => data(http.get<Paginated<Enrollment>>(`/courses/${id}/enrollments/`)),
  enrollStudent: (id: number, payload: { student_email: string; access_days?: number; group_id?: number | null }) =>
    data(http.post<Enrollment>(`/courses/${id}/enroll-student/`, payload)),
}

export const groupsApi = {
  list: (course: number) => data(http.get<Group[]>('/groups/', { params: { course } })),
  create: (payload: { course: number; name: string; max_students?: number }) => data(http.post<Group>('/groups/', payload)),
  update: (id: number, payload: Partial<Group>) => data(http.patch<Group>(`/groups/${id}/`, payload)),
  remove: (id: number) => http.delete(`/groups/${id}/`),
  students: (id: number) => data(http.get<GroupStudent[]>(`/groups/${id}/students/`)),
}
