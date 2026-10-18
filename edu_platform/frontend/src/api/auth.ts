import type {
  AuthSession,
  LoginResponse,
  Message,
  ParentRelation,
  TwoFactorSetup,
  UserProfile,
} from '@/types/api'

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
  is_minor?: boolean
  parent_consent?: boolean
}

const data = <T>(p: Promise<{ data: T }>) => p.then((r) => r.data)

export const authApi = {
  login: (payload: LoginPayload) => data(http.post<LoginResponse>('/auth/login/', payload)),
  register: (payload: RegisterPayload) => data(http.post<Message>('/auth/register/', payload)),
  registerByInvite: (payload: { invite_token: string; email: string; password: string; first_name: string; last_name: string }) =>
    data(http.post<Message>('/auth/register-by-invite/', payload)),
  logout: () => http.post('/auth/logout/', {}),
  logoutAll: () => http.post('/auth/logout-all/', {}),
  me: () => data(http.get<UserProfile>('/auth/users/me/')),
  updateMe: (payload: Partial<UserProfile>) => data(http.patch<UserProfile>('/auth/users/me/', payload)),
  changePassword: (old_password: string, new_password: string) =>
    data(http.post<Message>('/auth/change-password/', { old_password, new_password })),
  verifyEmail: (token: string) => data(http.get<Message>('/auth/verify-email/', { params: { token } })),
  resendVerification: () => data(http.post<Message>('/auth/verify-email/resend/', {})),
  requestPasswordReset: (email: string) => data(http.post<Message>('/auth/password-reset/', { email })),
  confirmPasswordReset: (token: string, new_password: string) =>
    data(http.post<Message>('/auth/password-reset/confirm/', { token, new_password })),
  sessions: () => data(http.get<AuthSession[]>('/auth/sessions/')),
  revokeSession: (id: number) => http.delete(`/auth/sessions/${id}/`),
  twoFactorSetup: () => data(http.post<TwoFactorSetup>('/auth/2fa/setup/', {})),
  twoFactorEnable: (code: string) =>
    data(http.post<{ message: string; backup_codes: string[] }>('/auth/2fa/enable/', { code })),
  twoFactorDisable: (password: string, code: string) => data(http.post<Message>('/auth/2fa/disable/', { password, code })),
}

export const parentsApi = {
  children: () => data(http.get<ParentRelation[]>('/parents/children/')),
  requestLink: (student_email: string) => data(http.post<ParentRelation>('/parents/children/', { student_email })),
  unlink: (id: number) => http.delete(`/parents/children/${id}/`),
  requests: () => data(http.get<ParentRelation[]>('/parents/requests/')),
  confirm: (id: number) => data(http.post<ParentRelation>(`/parents/requests/${id}/`, {})),
  reject: (id: number) => http.delete(`/parents/requests/${id}/`),
}
