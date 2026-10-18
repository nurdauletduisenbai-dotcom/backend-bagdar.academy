<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { notificationsApi } from '@/api/notifications'
import AppPager from '@/components/ui/AppPager.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAction, useAsync } from '@/composables/useAsync'
import { useNotificationsStore } from '@/stores/notifications'
import type { AppNotification } from '@/types/api'
import { fmtDateTime } from '@/utils/format'

const router = useRouter()
const store = useNotificationsStore()
const { act } = useAction()
const onlyUnread = ref(false)
const page = ref(1)
const list = useAsync(() => notificationsApi.list({ is_read: onlyUnread.value ? false : undefined, page: page.value }))

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
  <PageHeader title="Уведомления">
    <label class="inline"><input v-model="onlyUnread" type="checkbox" @change="page = 1; list.run()" /> Только непрочитанные</label>
    <button class="btn btn--ghost" @click="readAll">Прочитать все</button>
  </PageHeader>
  <StateBlock :loading="list.loading.value" :error="list.error.value" :empty="!list.data.value?.results.length"
              empty-text="Уведомлений нет." @retry="list.run">
    <ul class="list-plain">
      <li v-for="n in list.data.value?.results ?? []" :key="n.id" class="notification" :class="{ unread: !n.is_read }" @click="open(n)">
        <div class="row row--between">
          <strong>{{ n.title }}</strong>
          <span class="muted small">{{ fmtDateTime(n.created_at) }}</span>
        </div>
        <div v-if="n.message" class="small" style="white-space: pre-line">{{ n.message }}</div>
      </li>
    </ul>
    <AppPager :page="page" :total-pages="list.data.value?.total_pages ?? 1" @change="(p) => { page = p; list.run() }" />
  </StateBlock>
</template>

<style scoped>
.notification {
  cursor: pointer;
}
.unread {
  border-left: 4px solid var(--primary) !important;
}
</style>
