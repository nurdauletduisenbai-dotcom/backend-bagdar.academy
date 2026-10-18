<script setup lang="ts">
import { ref } from 'vue'

import { assignmentsApi } from '@/api/assignments'
import AppBadge from '@/components/ui/AppBadge.vue'
import AppPager from '@/components/ui/AppPager.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAsync } from '@/composables/useAsync'
import { useAuthStore } from '@/stores/auth'
import type { Assignment } from '@/types/api'
import { fmtDateTime, submissionStatusLabels } from '@/utils/format'

const auth = useAuthStore()
const page = ref(1)
const list = useAsync(() => assignmentsApi.list({ page: page.value }))

function status(a: Assignment) {
  if (a.my_submission) return a.my_submission.status
  return a.is_overdue ? 'overdue' : 'pending'
}
const kind = (s: string) => (s === 'graded' ? 'success' : s === 'overdue' ? 'danger' : s === 'pending' ? 'default' : 'warning')
</script>

<template>
  <PageHeader title="Домашние задания">
    <RouterLink v-if="auth.isTeacher" to="/teach/submissions" class="btn btn--ghost">Проверка работ</RouterLink>
  </PageHeader>
  <StateBlock :loading="list.loading.value" :error="list.error.value" :empty="!list.data.value?.results.length"
              empty-text="Заданий нет." @retry="list.run">
    <div class="card table-wrap">
      <table class="table">
        <thead><tr><th>Задание</th><th>Дедлайн</th><th>Статус</th><th>Оценка</th></tr></thead>
        <tbody>
          <tr v-for="a in list.data.value?.results ?? []" :key="a.id">
            <td><RouterLink :to="`/assignments/${a.id}`">{{ a.title }}</RouterLink></td>
            <td :class="{ error: a.is_overdue && !a.my_submission }">{{ fmtDateTime(a.deadline) }}</td>
            <td>
              <AppBadge v-if="auth.isStudent" :kind="kind(status(a))">{{ submissionStatusLabels[status(a)] }}</AppBadge>
              <span v-else class="muted small">сдач: {{ a.submissions_count ?? 0 }}</span>
            </td>
            <td>{{ a.my_submission?.score ?? '—' }} <span class="muted small">/ {{ a.max_score }}</span></td>
          </tr>
        </tbody>
      </table>
    </div>
    <AppPager :page="page" :total-pages="list.data.value?.total_pages ?? 1" @change="(p) => { page = p; list.run() }" />
  </StateBlock>
</template>
