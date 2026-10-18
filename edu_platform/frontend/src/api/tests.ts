import type {
  AttemptListItem,
  AttemptResult,
  AttemptStarted,
  Paginated,
  Question,
  TestInfo,
  TestQuestionManage,
  TestStats,
  Topic,
} from '@/types/api'

import { http } from './http'

const data = <T>(p: Promise<{ data: T }>) => p.then((r) => r.data)

export const testsApi = {
  list: (params: { course?: number; lesson?: number } = {}) => data(http.get<Paginated<TestInfo>>('/tests/', { params })),
  get: (id: number) => data(http.get<TestInfo>(`/tests/${id}/`)),
  create: (payload: Partial<TestInfo>) => data(http.post<TestInfo>('/tests/', payload)),
  update: (id: number, payload: Partial<TestInfo>) => data(http.patch<TestInfo>(`/tests/${id}/`, payload)),
  remove: (id: number) => http.delete(`/tests/${id}/`),
  questions: (id: number) => data(http.get<TestQuestionManage[]>(`/tests/${id}/questions/`)),
  addQuestion: (id: number, question_id: number, points = 1) =>
    data(http.post<TestQuestionManage>(`/tests/${id}/questions/`, { question_id, points })),
  updateQuestion: (id: number, questionId: number, payload: { points?: number; order?: number }) =>
    data(http.patch<TestQuestionManage>(`/tests/${id}/questions/${questionId}/`, payload)),
  removeQuestion: (id: number, questionId: number) => http.delete(`/tests/${id}/questions/${questionId}/`),
  stats: (id: number) => data(http.get<TestStats>(`/tests/${id}/stats/`)),
  attempts: (id: number) => data(http.get<AttemptListItem[]>(`/tests/${id}/attempts/`)),

  start: (id: number) => data(http.post<AttemptStarted>(`/tests/${id}/attempts/`, {})),
  attempt: (attemptId: number) => data(http.get<AttemptStarted | AttemptResult>(`/tests/attempts/${attemptId}/`)),
  saveAnswer: (attemptId: number, questionId: number, payload: { selected_options?: unknown; text_answer?: string }) =>
    http.put(`/tests/attempts/${attemptId}/answers/${questionId}/`, payload),
  logEvent: (attemptId: number, event_type: string, metadata: Record<string, unknown> = {}) =>
    http.post(`/tests/attempts/${attemptId}/events/`, { event_type, metadata }),
  submit: (attemptId: number) => data(http.post<AttemptResult>(`/tests/attempts/${attemptId}/submit/`, {})),
  grade: (attemptId: number, questionId: number, score: number, feedback = '') =>
    data(http.put<AttemptResult>(`/tests/attempts/${attemptId}/answers/${questionId}/grade/`, { score, feedback })),
}

export const questionsApi = {
  topics: () => data(http.get<Topic[]>('/topics/')),
  createTopic: (payload: { subject: string; name: string; parent?: number | null }) =>
    data(http.post<Topic>('/topics/', payload)),
  removeTopic: (id: number) => http.delete(`/topics/${id}/`),
  list: (params: Record<string, unknown> = {}) => data(http.get<Paginated<Question>>('/questions/', { params })),
  create: (payload: Partial<Question>) => data(http.post<Question>('/questions/', payload)),
  update: (id: number, payload: Partial<Question>) => data(http.patch<Question>(`/questions/${id}/`, payload)),
  remove: (id: number) => http.delete(`/questions/${id}/`),
}
