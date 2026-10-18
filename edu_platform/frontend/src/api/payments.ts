import type { Order, Paginated } from '@/types/api'

import { http } from './http'

const data = <T>(p: Promise<{ data: T }>) => p.then((r) => r.data)

export const paymentsApi = {
  list: (params: { status?: string; page?: number } = {}) => data(http.get<Paginated<Order>>('/payments/orders/', { params })),
  create: (course_id: number, provider: Order['provider'] = 'manual') =>
    data(http.post<Order>('/payments/orders/', { course_id, provider }, {
      headers: { 'Idempotency-Key': crypto.randomUUID() },
    })),
  markPaid: (id: number) => data(http.post<Order>(`/payments/orders/${id}/mark-paid/`, {})),
  refund: (id: number) => data(http.post<Order>(`/payments/orders/${id}/refund/`, {})),
  cancel: (id: number) => data(http.post<Order>(`/payments/orders/${id}/cancel/`, {})),
  providers: () => data(http.get<{ name: string; is_configured: boolean }[]>('/payments/orders/providers/')),
}
