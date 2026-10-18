import type { CourseProgressSummary, CourseReport, CourseStudentRow, OrgSummary } from '@/types/api'

import { http } from './http'

const data = <T>(p: Promise<{ data: T }>) => p.then((r) => r.data)

export const progressApi = {
  my: () => data(http.get<CourseProgressSummary[]>('/progress/my/')),
  course: (courseId: number, student?: number) =>
    data(http.get<CourseReport>(`/progress/courses/${courseId}/`, { params: student ? { student } : {} })),
  courseStudents: (courseId: number) => data(http.get<CourseStudentRow[]>(`/progress/courses/${courseId}/students/`)),
  student: (studentId: number) =>
    data(http.get<{ student_id: number; full_name: string; courses: CourseProgressSummary[] }>(
      `/progress/students/${studentId}/`)),
  orgSummary: () => data(http.get<OrgSummary>('/progress/org/summary/')),
}
