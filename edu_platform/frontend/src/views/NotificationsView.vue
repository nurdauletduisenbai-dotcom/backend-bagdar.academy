<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

import { notificationsApi } from '@/api/notifications'
import AppPager from '@/components/ui/AppPager.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAction, useAsync } from '@/composables/useAsync'
import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'
import type { AppNotification } from '@/types/api'

const router = useRouter()
const auth = useAuthStore()
const store = useNotificationsStore()
const { act } = useAction()
const page = ref(1)
const filter = ref<'all' | 'announce' | 'deadline' | 'grade'>('all')
const list = useAsync(() => notificationsApi.list({ page: page.value }))

const GROUPS: Record<string, string[]> = {
  announce: ['announcement', 'system'],
  deadline: ['assignment_new', 'assignment_deadline', 'session_start'],
  grade: ['assignment_graded', 'test_result'],
}
const items = computed(() =>
  (list.data.value?.results ?? []).filter((n) => filter.value === 'all' || GROUPS[filter.value].includes(n.type)),
)

function ago(iso: string) {
  const min = Math.round((Date.now() - new Date(iso).getTime()) / 60000)
  if (min < 1) return 'сейчас'
  if (min < 60) return `${min} мин`
  if (min < 24 * 60) return `${Math.round(min / 60)} ч`
  if (min < 48 * 60) return 'вчера'
  return new Date(iso).toLocaleDateString('ru-RU', { day: 'numeric', month: 'short' })
}

/** Куда ведёт уведомление (по metadata) */
function linkOf(n: AppNotification): string | null {
  const m = n.metadata as Record<string, number>
  if (m.assignment_id) return `/assignments/${m.assignment_id}`
  if (m.attempt_id) return `/attempts/${m.attempt_id}`
  if (m.lesson_id) return `/lessons/${m.lesson_id}`
  if (m.course_id) return `/courses/${m.course_id}`
  if (m.session_id) return '/schedule'
  if (m.announcement_id) return '/announcements'
  if (m.relation_id) return '/profile'
  if (m.order_id) return '/orders'
  return null
}

async function open(n: AppNotification) {
  if (!n.is_read) {
    await notificationsApi.read(n.id)
    store.refresh()
  }
  const link = linkOf(n)
  if (link) router.push(link)
  else list.run()
}

async function readAll() {
  await act(() => notificationsApi.readAll(), 'Все прочитаны')
  store.refresh()
  list.run()
}
</script>

<template>
  <PageHeader title="Входящие">
    <button class="btn btn--text btn--sm" @click="readAll">Прочитать всё</button>
    <RouterLink :to="{ path: '/profile', query: { tab: 'notifications' } }" class="btn btn--text btn--sm">Настройки</RouterLink>
  </PageHeader>

  <div class="pills" style="margin-bottom: var(--space-lg)">
    <button class="pill" :class="{ active: filter === 'all' }" @click="filter = 'all'">Все <span class="count">{{ list.data.value?.total ?? 0 }}</span></button>
    <button class="pill" :class="{ active: filter === 'announce' }" @click="filter = 'announce'">Объявления</button>
    <button class="pill" :class="{ active: filter === 'deadline' }" @click="filter = 'deadline'">Дедлайны</button>
    <button class="pill" :class="{ active: filter === 'grade' }" @click="filter = 'grade'">Оценки</button>
  </div>

  <StateBlock :loading="list.loading.value" :error="list.error.value" :empty="!items.length" empty-text="Здесь пока пусто" @retry="list.run">
    <div class="card card--flush">
      <button v-for="n in items" :key="n.id" class="inbox-row" :class="{ unread: !n.is_read }" @click="open(n)">
        <span class="dot" :class="{ read: n.is_read }" />
        <span class="inbox-row__body">
          <strong>{{ n.title }}</strong>
          <span v-if="n.message" class="muted small">{{ n.message }}</span>
        </span>
        <span class="muted small">{{ ago(n.created_at) }}</span>
      </button>
    </div>
    <AppPager :page="page" :total-pages="list.data.value?.total_pages ?? 1" @change="(p) => { page = p; list.run() }" />
  </StateBlock>

  <RouterLink v-if="auth.isTeacher" to="/announcements" class="dropzone announce-cta">
    Учитель / админ: «+ Объявление» — текст и аудитория (школа или курс)
  </RouterLink>
</template>

<style scoped>
.inbox-row {
  width: 100%;
  display: grid;
  grid-template-columns: 8px minmax(0, 1fr) auto;
  gap: var(--space-md);
  align-items: center;
  padding: var(--space-md) var(--space-xl);
  border: 0;
  border-bottom: 1px solid var(--border-default);
  background: none;
  text-align: left;
  font: inherit;
  color: inherit;
  cursor: pointer;
}
.inbox-row:last-child {
  border-bottom: 0;
}
.inbox-row:hover {
  background: var(--surface-subtle);
}
.inbox-row:not(.unread) strong {
  font-weight: 400;
  color: var(--text-secondary);
}
.inbox-row__body {
  display: grid;
  gap: 2px;
  min-width: 0;
}
.inbox-row__body .small {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.dot.read {
  background: transparent;
}
.announce-cta {
  display: block;
  margin-top: var(--space-lg);
  color: var(--text-secondary);
  text-decoration: none;
}
</style>
