<script setup lang="ts">
import { progressApi } from '@/api/progress'
import PageHeader from '@/components/ui/PageHeader.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAsync } from '@/composables/useAsync'
import { courseStatusLabels, fmtMoney, roleLabels } from '@/utils/format'
import type { Role } from '@/types/api'

const summary = useAsync(() => progressApi.orgSummary())
</script>

<template>
  <PageHeader title="Сводка по школе" />
  <StateBlock :loading="summary.loading.value" :error="summary.error.value" @retry="summary.run">
    <template v-if="summary.data.value">
      <div class="grid" style="margin-bottom: 16px">
        <div class="card"><div class="stat">{{ summary.data.value.active_enrollments }}</div><span class="muted">активных записей</span></div>
        <div class="card"><div class="stat">{{ summary.data.value.average_progress_pct }}%</div><span class="muted">средний прогресс</span></div>
        <div class="card"><div class="stat">{{ fmtMoney(summary.data.value.revenue_30d) }}</div><span class="muted">выручка за 30 дней</span></div>
        <div class="card"><div class="stat">{{ fmtMoney(summary.data.value.revenue_total) }}</div><span class="muted">выручка всего</span></div>
        <RouterLink to="/admin/orders" class="card card--link"><div class="stat">{{ summary.data.value.orders_pending }}</div><span class="muted">заказов ждут подтверждения →</span></RouterLink>
      </div>
      <div class="grid--2">
        <section class="card">
          <h2>Участники</h2>
          <ul class="list-plain">
            <li v-for="(n, role) in summary.data.value.members_by_role" :key="role" class="row row--between">
              <span>{{ roleLabels[role as Role] ?? role }}</span><strong>{{ n }}</strong>
            </li>
          </ul>
          <RouterLink to="/admin/members" class="small">Управлять →</RouterLink>
        </section>
        <section class="card">
          <h2>Курсы</h2>
          <ul class="list-plain">
            <li v-for="(n, status) in summary.data.value.courses_by_status" :key="status" class="row row--between">
              <span>{{ courseStatusLabels[status] ?? status }}</span><strong>{{ n }}</strong>
            </li>
          </ul>
          <RouterLink to="/teach/courses" class="small">Все курсы →</RouterLink>
        </section>
      </div>
    </template>
  </StateBlock>
</template>
