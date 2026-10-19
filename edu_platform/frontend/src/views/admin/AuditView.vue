<script setup lang="ts">
import { reactive } from 'vue'

import { orgsApi } from '@/api/orgs'
import AppPager from '@/components/ui/AppPager.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAsync } from '@/composables/useAsync'
import { fmtDateTime } from '@/utils/format'

const actions: Record<string, string> = {
  login: 'Вход', logout: 'Выход', password_change: 'Смена пароля', password_reset: 'Сброс пароля',
  role_change: 'Изменение ролей', member_deactivate: 'Отключение участника', course_create: 'Создание курса',
  course_delete: 'Удаление курса', payment_paid: 'Оплата', payment_refund: 'Возврат', grade_change: 'Оценка',
}
const filters = reactive({ action: '', page: 1 })
const logs = useAsync(() => orgsApi.auditLogs({ action: filters.action || undefined, page: filters.page }))
</script>

<template>
  <PageHeader title="Журнал аудита" subtitle="Критичные действия в школе" />
  <select v-model="filters.action" style="max-width: 260px; margin-bottom: var(--space-lg)" @change="filters.page = 1; logs.run()">
    <option value="">Все действия</option>
    <option v-for="(label, key) in actions" :key="key" :value="key">{{ label }}</option>
  </select>
  <StateBlock :loading="logs.loading.value" :error="logs.error.value" :empty="!logs.data.value?.results.length" @retry="logs.run">
    <div class="card card--flush table-wrap">
      <table class="table">
        <thead><tr><th>Время</th><th>Действие</th><th>Кто</th><th>IP</th><th>Объект</th><th>Детали</th></tr></thead>
        <tbody>
          <tr v-for="l in logs.data.value?.results ?? []" :key="l.id">
            <td class="small nowrap">{{ fmtDateTime(l.created_at) }}</td>
            <td><span class="badge">{{ actions[l.action] ?? l.action }}</span></td>
            <td>{{ l.user_email ?? '—' }}</td>
            <td class="small">{{ l.ip_address ?? '—' }}</td>
            <td class="small">{{ l.entity_type }} {{ l.entity_id ?? '' }}</td>
            <td><pre v-if="Object.keys(l.changes).length" class="code">{{ JSON.stringify(l.changes) }}</pre></td>
          </tr>
        </tbody>
      </table>
    </div>
    <AppPager :page="filters.page" :total-pages="logs.data.value?.total_pages ?? 1" @change="(p) => { filters.page = p; logs.run() }" />
  </StateBlock>
</template>

<style scoped>
.nowrap {
  white-space: nowrap;
}
</style>
