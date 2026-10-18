import type { OrganizationBrief } from '@/types/api'

import { http } from './http'

export const orgsApi = {
  my: () => http.get<OrganizationBrief[]>('/orgs/my/').then((r) => r.data),
}
