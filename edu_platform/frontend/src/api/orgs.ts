import type { AuditLog, Invite, Member, Organization, OrganizationBrief, Paginated, Role } from '@/types/api'

import { http } from './http'

const data = <T>(p: Promise<{ data: T }>) => p.then((r) => r.data)

export const orgsApi = {
  my: () => data(http.get<OrganizationBrief[]>('/orgs/my/')),
  current: () => data(http.get<Organization>('/orgs/current/')),
  updateCurrent: (payload: Partial<Organization>) => data(http.patch<Organization>('/orgs/current/', payload)),
  members: (params: Record<string, unknown> = {}) => data(http.get<Paginated<Member>>('/orgs/members/', { params })),
  addMember: (email: string, role: Role) => data(http.post<Member>('/orgs/members/', { email, role })),
  updateMember: (id: number, payload: Partial<Pick<Member, 'role' | 'is_active'>>) =>
    data(http.patch<Member>(`/orgs/members/${id}/`, payload)),
  deactivateMember: (id: number) => http.delete(`/orgs/members/${id}/`),
  invites: () => data(http.get<Paginated<Invite>>('/orgs/invites/list/')),
  createInvite: (payload: { role: Role; course_id?: number | null; group_id?: number | null; max_uses?: number; expires_in_days?: number }) =>
    data(http.post<Invite>('/orgs/invites/', payload)),
  revokeInvite: (id: number) => http.delete(`/orgs/invites/${id}/`),
  auditLogs: (params: Record<string, unknown> = {}) => data(http.get<Paginated<AuditLog>>('/audit/logs/', { params })),
}
