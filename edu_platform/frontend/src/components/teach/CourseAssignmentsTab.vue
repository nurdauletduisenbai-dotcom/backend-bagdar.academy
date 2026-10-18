<script setup lang="ts">
import { reactive } from 'vue'

import { assignmentsApi } from '@/api/assignments'
import { lessonsApi } from '@/api/content'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAction, useAsync } from '@/composables/useAsync'
import { fmtDateTime, fromLocalInput } from '@/utils/format'

const props = defineProps<{ courseId: number }>()
const { act, busy } = useAction()
const assignments = useAsync(() => assignmentsApi.list({ course: props.courseId }))
const lessons = useAsync(() => lessonsApi.list({ course: props.courseId }))
const form = reactive({ lesson: 0, title: '', description: '', deadline: '', max_score: 10, accept_late: true })

async function create() {
  const ok = await act(() => assignmentsApi.create({ ...form, deadline: fromLocalInput(form.deadline)! }),
    'Задание создано — ученики получили уведомление')
  if (ok) {
    Object.assign(form, { title: '', description: '', deadline: '' })
    assignments.run()
  }
}

async function remove(id: number) {
  if (!confirm('Удалить задание и все сдачи?')) return
  if (await act(() => assignmentsApi.remove(id), 'Удалено')) assignments.run()
}
</script>

<template>
  <div class="grid--2" style="align-items: start">
    <section class="card">
      <h2>Задания курса</h2>
      <StateBlock :loading="assignments.loading.value" :error="assignments.error.value"
                  :empty="!assignments.data.value?.results.length" @retry="assignments.run">
        <ul class="list-plain">
          <li v-for="a in assignments.data.value?.results ?? []" :key="a.id" class="row row--between">
            <span>
              <RouterLink :to="`/assignments/${a.id}`">{{ a.title }}</RouterLink>
              <div class="muted small">до {{ fmtDateTime(a.deadline) }} · сдач: {{ a.submissions_count ?? 0 }}</div>
            </span>
            <span class="row">
              <RouterLink :to="{ path: '/teach/submissions', query: { assignment: a.id } }" class="btn btn--ghost btn--sm">Проверить</RouterLink>
              <button class="btn btn--ghost btn--sm" @click="remove(a.id)">Удалить</button>
            </span>
          </li>
        </ul>
      </StateBlock>
    </section>
    <section class="card">
      <h2>Новое задание</h2>
      <form class="form" @submit.prevent="create">
        <label>
          Урок
          <select v-model.number="form.lesson" required>
            <option :value="0" disabled>— выберите урок —</option>
            <option v-for="l in lessons.data.value ?? []" :key="l.id" :value="l.id">{{ l.title }}</option>
          </select>
        </label>
        <label>Название <input v-model="form.title" required /></label>
        <label>Описание <textarea v-model="form.description" required /></label>
        <div class="form-row">
          <label>Дедлайн <input v-model="form.deadline" type="datetime-local" required /></label>
          <label>Макс. балл <input v-model.number="form.max_score" type="number" min="1" /></label>
        </div>
        <label class="inline"><input v-model="form.accept_late" type="checkbox" /> Принимать после дедлайна</label>
        <button class="btn" :disabled="busy || !form.lesson" style="justify-self: start">Создать</button>
      </form>
    </section>
  </div>
</template>
