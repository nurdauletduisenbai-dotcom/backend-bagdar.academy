import type { Comment, Lesson, LessonDetail, Material, Paginated, Section, VideoManage, VideoPlayer } from '@/types/api'

import { http, toFormData } from './http'

const data = <T>(p: Promise<{ data: T }>) => p.then((r) => r.data)

export const sectionsApi = {
  list: (course: number) => data(http.get<Section[]>('/sections/', { params: { course } })),
  create: (payload: { course: number; title: string; order?: number }) => data(http.post<Section>('/sections/', payload)),
  update: (id: number, payload: Partial<Section>) => data(http.patch<Section>(`/sections/${id}/`, payload)),
  remove: (id: number) => http.delete(`/sections/${id}/`),
}

export const lessonsApi = {
  list: (params: { course?: number; section?: number }) => data(http.get<Lesson[]>('/lessons/', { params })),
  get: (id: number) => data(http.get<LessonDetail>(`/lessons/${id}/`)),
  create: (payload: Partial<Lesson> & { section: number; title: string }) => data(http.post<Lesson>('/lessons/', payload)),
  update: (id: number, payload: Partial<Lesson>) => data(http.patch<Lesson>(`/lessons/${id}/`, payload)),
  remove: (id: number) => http.delete(`/lessons/${id}/`),
  complete: (id: number) => data(http.post<{ is_completed: boolean }>(`/lessons/${id}/complete/`, {})),
}

export const materialsApi = {
  list: (lesson: number) => data(http.get<Material[]>('/materials/', { params: { lesson } })),
  create: (payload: { lesson: number; title: string; file?: File | null; file_url?: string }) =>
    data(http.post<Material>('/materials/', toFormData(payload))),
  remove: (id: number) => http.delete(`/materials/${id}/`),
}

export const videosApi = {
  list: (lesson: number) => data(http.get<VideoManage[]>('/videos/', { params: { lesson } })),
  create: (payload: { lesson: number; title: string; youtube_url: string; duration_seconds?: number }) =>
    data(http.post<VideoManage>('/videos/', payload)),
  update: (id: number, payload: Partial<VideoManage> & { youtube_url?: string }) =>
    data(http.patch<VideoManage>(`/videos/${id}/`, payload)),
  remove: (id: number) => http.delete(`/videos/${id}/`),
  play: (id: number) => data(http.get<VideoPlayer>(`/videos/${id}/play/`)),
  progress: (id: number, watched_seconds: number) =>
    data(http.put<{ watched_seconds: number; is_completed: boolean; progress_percent: number }>(
      `/videos/${id}/progress/`, { watched_seconds })),
}

export const commentsApi = {
  list: (lesson: number, page = 1) => data(http.get<Paginated<Comment>>('/comments/', { params: { lesson, page } })),
  create: (payload: { lesson: number; content: string; parent?: number | null }) =>
    data(http.post<Comment>('/comments/', payload)),
  update: (id: number, content: string) => data(http.patch<Comment>(`/comments/${id}/`, { content })),
  remove: (id: number) => http.delete(`/comments/${id}/`),
  toggleHidden: (id: number) => data(http.post<Comment>(`/comments/${id}/toggle-hidden/`, {})),
}
