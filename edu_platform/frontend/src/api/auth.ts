import type { LoginResponse, UserProfile } from '@/types/api'

import { http } from './http'

export interface LoginPayload {
  email: string
  password: string
  totp_code?: string
}

export interface RegisterPayload {
  email: string
  password: string
  first_name: string
  last_name: string
  role?: 'student' | 'parent'
  org_slug?: string
}

export const authApi = {
  login: (payload: LoginPayload) => http.post<LoginResponse>('/auth/login/', payload).then((r) => r.data),
  register: (payload: RegisterPayload) => http.post('/auth/register/', payload).then((r) => r.data),
  logout: () => http.post('/auth/logout/', {}),
  me: () => http.get<UserProfile>('/auth/users/me/').then((r) => r.data),
}
