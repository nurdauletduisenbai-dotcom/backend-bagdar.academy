import type { Course, Paginated } from '@/types/api'

import { http } from './http'

export interface CourseFilters {
  search?: string
  type?: Course['type']
  page?: number
}

export const coursesApi = {
  list: (params: CourseFilters = {}) =>
    http.get<Paginated<Course>>('/courses/', { params }).then((r) => r.data),
  get: (id: number) => http.get<Course>(`/courses/${id}/`).then((r) => r.data),
}
