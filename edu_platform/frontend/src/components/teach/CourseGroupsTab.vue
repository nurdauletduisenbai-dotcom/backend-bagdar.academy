<script setup lang="ts">
import { reactive, ref } from 'vue'

import { groupsApi } from '@/api/courses'
import { sessionsApi } from '@/api/schedule'
import AppModal from '@/components/ui/AppModal.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAction, useAsync } from '@/composables/useAsync'
import type { Group, GroupStudent } from '@/types/api'
import { fromLocalInput } from '@/utils/format'

const props = defineProps<{ courseId: number }>()
const { act, busy } = useAction()
const groups = useAsync(() => groupsApi.list(props.courseId))
const newGroup = reactive({ name: '', max_students: 30 })
const viewing = ref<{ group: Group; students: GroupStudent[] } | null>(null)
const session = reactive({ group: 0, title: '', start_time: '', end_time: '', location: '', online_meeting_url: '' })

async function addGroup() {
  if (await act(() => groupsApi.create({ course: props.courseId, ...newGroup }), 'Группа создана')) {
    newGroup.name = ''
    groups.run()
  }
}

async function showStudents(group: Group) {
  const students = await act(() => groupsApi.students(group.id))
  if (students) viewing.value = { group, students }
}

async function addSession() {
  const ok = await act(() => sessionsApi.create({
    ...session,
    start_time: fromLocalInput(session.start_time)!,
    end_time: fromLocalInput(session.end_time)!,
    online_meeting_url: session.online_meeting_url || null,
  }), 'Занятие добавлено в расписание')
  if (ok) Object.assign(session, { title: '', start_time: '', end_time: '' })
}
</script>

<template>
  <div class="grid--2" style="align-items: start">
    <section class="card">
      <h2>Группы</h2>
      <StateBlock :loading="groups.loading.value" :error="groups.error.value" :empty="!groups.data.value?.length" @retry="groups.run">
        <ul class="list-plain">
          <li v-for="g in groups.data.value ?? []" :key="g.id" class="row row--between">
            <span>{{ g.name }} <span class="muted small">{{ g.students_count }}/{{ g.max_students }}</span></span>
            <button class="btn btn--ghost btn--sm" @click="showStudents(g)">Ученики</button>
          </li>
        </ul>
      </StateBlock>
      <form class="row" style="margin-top: 12px" @submit.prevent="addGroup">
        <input v-model="newGroup.name" placeholder="Название группы" style="max-width: 220px" required />
        <input v-model.number="newGroup.max_students" type="number" min="1" style="max-width: 90px" title="Мест" />
        <button class="btn btn--ghost" :disabled="busy">+ Группа</button>
      </form>
      <p class="muted small">Ученика в группу добавляют на вкладке «Ученики» при записи.</p>
    </section>

    <section class="card">
      <h2>Добавить занятие</h2>
      <form class="form" @submit.prevent="addSession">
        <label>
          Группа
          <select v-model.number="session.group" required>
            <option :value="0" disabled>— выберите —</option>
            <option v-for="g in groups.data.value ?? []" :key="g.id" :value="g.id">{{ g.name }}</option>
          </select>
        </label>
        <label>Тема <input v-model="session.title" required /></label>
        <div class="form-row">
          <label>Начало <input v-model="session.start_time" type="datetime-local" required /></label>
          <label>Конец <input v-model="session.end_time" type="datetime-local" required /></label>
        </div>
        <div class="form-row">
          <label>Аудитория <input v-model="session.location" /></label>
          <label>Ссылка (Zoom/Meet) <input v-model="session.online_meeting_url" type="url" /></label>
        </div>
        <button class="btn" :disabled="busy || !session.group" style="justify-self: start">Добавить</button>
      </form>
    </section>
  </div>

  <AppModal v-if="viewing" :title="`Группа ${viewing.group.name}`" @close="viewing = null">
    <ul v-if="viewing.students.length" class="list-plain">
      <li v-for="s in viewing.students" :key="s.student_id">{{ s.full_name }} <span class="muted small">{{ s.email }}</span></li>
    </ul>
    <p v-else class="muted">В группе пока нет учеников.</p>
  </AppModal>
</template>
