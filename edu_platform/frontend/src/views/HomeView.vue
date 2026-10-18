<script setup lang="ts">
import { computed } from 'vue'

import { parentsApi } from '@/api/auth'
import { assignmentsApi, submissionsApi } from '@/api/assignments'
import { announcementsApi } from '@/api/notifications'
import { progressApi } from '@/api/progress'
import { sessionsApi } from '@/api/schedule'
import PageHeader from '@/components/ui/PageHeader.vue'
import ProgressBar from '@/components/ui/ProgressBar.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAsync } from '@/composables/useAsync'
import { useAuthStore } from '@/stores/auth'
import { fmtDateTime, fmtMoney } from '@/utils/format'

const auth = useAuthStore()
const now = new Date()
const inWeek = new Date(now.getTime() + 7 * 86400_000)

const sessions = useAsync(() => sessionsApi.list({ date_from: now.toISOString(), date_to: inWeek.toISOString() }))
const announcements = useAsync(() => announcementsApi.list())
const progress = useAsync(() => (auth.isStudent ? progressApi.my() : Promise.resolve([])))
const assignments = useAsync(() => (auth.isStudent ? assignmentsApi.list() : Promise.resolve(null)))
const toReview = useAsync(() => (auth.isTeacher ? submissionsApi.list({ status: 'submitted' }) : Promise.resolve(null)))
const children = useAsync(() => (auth.isParent ? parentsApi.children() : Promise.resolve([])))
const summary = useAsync(() => (auth.isAdmin ? progressApi.orgSummary() : Promise.resolve(null)))

const pending = computed(() =>
  (assignments.data.value?.results ?? []).filter((a) => !a.my_submission && !a.is_overdue).slice(0, 5),
)
</script>

<template>
  <PageHeader :title="`Здравствуйте, ${auth.user?.full_name?.split(' ')[0] ?? ''}!`" :subtitle="auth.currentOrg?.name" />

  <div class="grid--2" style="align-items: start">
    <!-- Администратор -->
    <section v-if="auth.isAdmin" class="card">
      <h2>Школа сегодня</h2>
      <StateBlock :loading="summary.loading.value" :error="summary.error.value" @retry="summary.run">
        <div v-if="summary.data.value" class="grid" style="grid-template-columns: repeat(auto-fill, minmax(120px, 1fr))">
          <div><div class="stat">{{ summary.data.value.members_by_role.student ?? 0 }}</div><span class="muted small">учеников</span></div>
          <div><div class="stat">{{ summary.data.value.active_enrollments }}</div><span class="muted small">активных записей</span></div>
          <div><div class="stat">{{ summary.data.value.orders_pending }}</div><span class="muted small">заказов ждут</span></div>
          <div><div class="stat">{{ fmtMoney(summary.data.value.revenue_30d) }}</div><span class="muted small">за 30 дней</span></div>
        </div>
        <RouterLink to="/admin" class="small">Подробная сводка →</RouterLink>
      </StateBlock>
    </section>

    <!-- Учитель -->
    <section v-if="auth.isTeacher" class="card">
      <h2>Ждут проверки</h2>
      <StateBlock :loading="toReview.loading.value" :error="toReview.error.value"
                  :empty="!toReview.data.value?.results.length" empty-text="Все работы проверены 🎉" @retry="toReview.run">
        <ul class="list-plain">
          <li v-for="s in toReview.data.value?.results.slice(0, 5) ?? []" :key="s.id" class="row row--between">
            <span>{{ s.student_name }} — {{ s.assignment_title }}</span>
            <span class="muted small">{{ fmtDateTime(s.submitted_at) }}</span>
          </li>
        </ul>
        <RouterLink to="/teach/submissions" class="small">Все работы ({{ toReview.data.value?.total }}) →</RouterLink>
      </StateBlock>
    </section>

    <!-- Ученик -->
    <section v-if="auth.isStudent" class="card">
      <h2>Мои курсы</h2>
      <StateBlock :loading="progress.loading.value" :error="progress.error.value" :empty="!progress.data.value?.length"
                  empty-text="Вы пока не записаны на курсы." @retry="progress.run">
        <ul class="list-plain">
          <li v-for="c in progress.data.value ?? []" :key="c.course_id" class="stack" style="gap: 6px">
            <RouterLink :to="`/courses/${c.course_id}`">{{ c.course_title }}</RouterLink>
            <ProgressBar :value="c.percent_completed" />
          </li>
        </ul>
      </StateBlock>
      <RouterLink to="/catalog" class="small">Каталог курсов →</RouterLink>
    </section>

    <section v-if="auth.isStudent" class="card">
      <h2>Нужно сдать</h2>
      <StateBlock :loading="assignments.loading.value" :error="assignments.error.value" :empty="!pending.length"
                  empty-text="Несданных заданий нет." @retry="assignments.run">
        <ul class="list-plain">
          <li v-for="a in pending" :key="a.id" class="row row--between">
            <RouterLink :to="`/assignments/${a.id}`">{{ a.title }}</RouterLink>
            <span class="muted small">до {{ fmtDateTime(a.deadline) }}</span>
          </li>
        </ul>
      </StateBlock>
    </section>

    <!-- Родитель -->
    <section v-if="auth.isParent" class="card">
      <h2>Мои дети</h2>
      <StateBlock :loading="children.loading.value" :error="children.error.value" :empty="!children.data.value?.length"
                  empty-text="Привяжите ребёнка в разделе «Мои дети»." @retry="children.run">
        <ul class="list-plain">
          <li v-for="r in children.data.value ?? []" :key="r.id" class="row row--between">
            <span>{{ r.student.full_name }}</span>
            <RouterLink v-if="r.is_confirmed" to="/children" class="small">Успеваемость →</RouterLink>
            <span v-else class="muted small">ждёт подтверждения</span>
          </li>
        </ul>
      </StateBlock>
    </section>

    <section class="card">
      <h2>Ближайшие занятия</h2>
      <StateBlock :loading="sessions.loading.value" :error="sessions.error.value" :empty="!sessions.data.value?.results.length"
                  empty-text="На этой неделе занятий нет." @retry="sessions.run">
        <ul class="list-plain">
          <li v-for="s in sessions.data.value?.results.slice(0, 5) ?? []" :key="s.id" class="row row--between">
            <span>{{ s.title }} <span class="muted small">{{ s.group_name }}</span></span>
            <span class="small">{{ fmtDateTime(s.start_time) }}</span>
          </li>
        </ul>
      </StateBlock>
      <RouterLink to="/schedule" class="small">Расписание →</RouterLink>
    </section>

    <section class="card">
      <h2>Объявления</h2>
      <StateBlock :loading="announcements.loading.value" :error="announcements.error.value"
                  :empty="!announcements.data.value?.results.length" @retry="announcements.run">
        <ul class="list-plain">
          <li v-for="a in announcements.data.value?.results.slice(0, 3) ?? []" :key="a.id">
            <strong>{{ a.title }}</strong>
            <div class="muted small">{{ a.author }} · {{ fmtDateTime(a.created_at) }}</div>
          </li>
        </ul>
      </StateBlock>
      <RouterLink to="/announcements" class="small">Все объявления →</RouterLink>
    </section>
  </div>
</template>
