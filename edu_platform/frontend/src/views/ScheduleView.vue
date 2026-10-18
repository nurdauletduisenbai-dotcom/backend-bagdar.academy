<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

import { groupsApi } from '@/api/courses'
import { sessionsApi } from '@/api/schedule'
import AppBadge from '@/components/ui/AppBadge.vue'
import AppModal from '@/components/ui/AppModal.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAction, useAsync } from '@/composables/useAsync'
import { useAuthStore } from '@/stores/auth'
import type { AttendanceStatus, ClassSession, GroupStudent } from '@/types/api'
import { attendanceLabels, fmtTime } from '@/utils/format'

const auth = useAuthStore()
const { act, busy } = useAction()

// Неделя, начиная с понедельника
const weekStart = ref(startOfWeek(new Date()))
function startOfWeek(d: Date) {
  const r = new Date(d)
  r.setHours(0, 0, 0, 0)
  r.setDate(r.getDate() - ((r.getDay() + 6) % 7))
  return r
}
const weekEnd = computed(() => new Date(weekStart.value.getTime() + 7 * 86400_000))
const sessions = useAsync(() => sessionsApi.list({
  date_from: weekStart.value.toISOString(), date_to: weekEnd.value.toISOString(),
}))

const days = computed(() => Array.from({ length: 7 }, (_, i) => {
  const date = new Date(weekStart.value.getTime() + i * 86400_000)
  return {
    date,
    label: date.toLocaleDateString('ru-RU', { weekday: 'long', day: 'numeric', month: 'long' }),
    items: (sessions.data.value?.results ?? []).filter((s) => new Date(s.start_time).toDateString() === date.toDateString()),
  }
}))

function shift(weeks: number) {
  weekStart.value = new Date(weekStart.value.getTime() + weeks * 7 * 86400_000)
  sessions.run()
}

async function toggleCancel(s: ClassSession) {
  if (!s.is_canceled && !confirm('Отменить занятие? Ученики получат уведомление.')) return
  if (await act(() => sessionsApi.update(s.id, { is_canceled: !s.is_canceled }), s.is_canceled ? 'Занятие восстановлено' : 'Занятие отменено')) {
    sessions.run()
  }
}

// ---------- Посещаемость ----------
const marking = ref<{ session: ClassSession; students: GroupStudent[] } | null>(null)
const marks = reactive<Record<number, AttendanceStatus>>({})

async function openAttendance(s: ClassSession) {
  const [students, existing] = await Promise.all([groupsApi.students(s.group), sessionsApi.attendance(s.id)])
  for (const st of students) marks[st.student_id] = existing.find((e) => e.student === st.student_id)?.status ?? 'present'
  marking.value = { session: s, students }
}

async function saveAttendance() {
  if (!marking.value) return
  const records = marking.value.students.map((s) => ({ student_id: s.student_id, status: marks[s.student_id] }))
  if (await act(() => sessionsApi.markAttendance(marking.value!.session.id, records), 'Посещаемость сохранена')) marking.value = null
}
</script>

<template>
  <PageHeader title="Расписание" :subtitle="`${weekStart.toLocaleDateString('ru-RU')} — ${new Date(weekEnd.getTime() - 1).toLocaleDateString('ru-RU')}`">
    <button class="btn btn--ghost" @click="shift(-1)">← Неделя</button>
    <button class="btn btn--ghost" @click="weekStart = startOfWeek(new Date()); sessions.run()">Сегодня</button>
    <button class="btn btn--ghost" @click="shift(1)">Неделя →</button>
  </PageHeader>

  <p v-if="auth.isTeacher" class="muted small">Занятия добавляются в редакторе курса → «Группы и расписание».</p>

  <StateBlock :loading="sessions.loading.value" :error="sessions.error.value" @retry="sessions.run">
    <div class="stack">
      <section v-for="day in days" :key="day.label" class="card">
        <h3 style="text-transform: capitalize">{{ day.label }}</h3>
        <p v-if="!day.items.length" class="muted small" style="margin: 0">Занятий нет</p>
        <ul v-else class="list-plain">
          <li v-for="s in day.items" :key="s.id" class="row row--between">
            <span>
              <strong>{{ fmtTime(s.start_time) }}–{{ fmtTime(s.end_time) }}</strong> {{ s.title }}
              <span class="muted small">· {{ s.group_name }}<template v-if="s.location"> · {{ s.location }}</template></span>
              <AppBadge v-if="s.is_canceled" kind="danger">Отменено</AppBadge>
            </span>
            <span class="row">
              <a v-if="s.online_meeting_url && !s.is_canceled" :href="s.online_meeting_url" target="_blank" rel="noopener" class="btn btn--sm">Подключиться</a>
              <template v-if="auth.isTeacher">
                <button class="btn btn--ghost btn--sm" @click="openAttendance(s)">Посещаемость</button>
                <button class="btn btn--ghost btn--sm" @click="toggleCancel(s)">{{ s.is_canceled ? 'Вернуть' : 'Отменить' }}</button>
              </template>
            </span>
          </li>
        </ul>
      </section>
    </div>
  </StateBlock>

  <AppModal v-if="marking" :title="`Посещаемость: ${marking.session.title}`" @close="marking = null">
    <p v-if="!marking.students.length" class="muted">В группе нет учеников.</p>
    <form v-else class="form" @submit.prevent="saveAttendance">
      <div v-for="st in marking.students" :key="st.student_id" class="row row--between">
        <span>{{ st.full_name }}</span>
        <select v-model="marks[st.student_id]" style="max-width: 180px">
          <option v-for="(label, key) in attendanceLabels" :key="key" :value="key">{{ label }}</option>
        </select>
      </div>
      <button class="btn" :disabled="busy" style="justify-self: start">Сохранить</button>
    </form>
  </AppModal>
</template>
