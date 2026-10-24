import type { NewsCategory, NewsPost, NewsPostDetail, Paginated, PlatformStats } from '@/types/api'

import { http } from './http'

const data = <T>(p: Promise<{ data: T }>) => p.then((r) => r.data)

export interface NewsFilters {
  category?: NewsCategory
  page?: number
  page_size?: number
}

/** Публичные новости и цифры для главной страницы — работают без входа */
export const newsApi = {
  list: (params: NewsFilters = {}) => data(http.get<Paginated<NewsPost>>('/news/posts/', { params })),
  get: (slug: string) => data(http.get<NewsPostDetail>(`/news/posts/${encodeURIComponent(slug)}/`)),
  stats: () => data(http.get<PlatformStats>('/news/stats/')),
}

/** Адрес обложки с учётом VITE_API_BASE_URL (бэкенд может жить на другом домене) */
export const coverSrc = (post: Pick<NewsPost, 'slug' | 'cover_url'>) =>
  post.cover_url ? `${http.defaults.baseURL}/news/posts/${encodeURIComponent(post.slug)}/cover/` : null
