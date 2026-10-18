<script setup lang="ts">
import { ref } from 'vue'

import { parentsApi } from '@/api/auth'
import { progressApi } from '@/api/progress'
import PageHeader from '@/components/ui/PageHeader.vue'
import ProgressBar from '@/components/ui/ProgressBar.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAction, useAsync } from '@/composables/useAsync'
import type { CourseProgressSummary } from '@/types/api'

const { act, busy } = useAction()
const children = useAsync(() => parentsApi.children())
const email = ref('')
const progress = ref<Record<number, CourseProgressSummary[]>>({})

async function link() {
  if (await act(() => parentsApi.requestLink(email.value), 'Запрос отправлен — ребёнок должен подтвердить его в профиле')) {
    email.value = ''
    children.run()
  }
}

async function unlink(id: number) {
  if (confirm('Отвязать ребёнка?') && (await act(() => parentsApi.unlink(id), 'Отвязано'))) children.run()
}

async function loadProgress(studentId: number) {
  const data = await act(() => progressApi.student(studentId))
  if (data) progress.value[studentId] = data.courses
}
</script>

<template>
  <PageHeader title="Мои дети" subtitle="Успеваемость видна после того, как ребёнок подтвердит запрос в своём профиле." />

  <form class="card row" style="margin-bottom: 16px" @submit.prevent="link">
    <input v-model="email" type="email" placeholder="email ученика" style="max-width: 300px" required />
    <button class="btn" :disabled="busy">Привязать ребёнка</button>
  </form>

  <StateBlock :loading="children.loading.value" :error="children.error.value" :empty="!children.data.value?.length" @retry="children.run">
    <div class="stack">
      <section v-for="r in children.data.value ?? []" :key="r.id" class="card">
        <div class="row row--between">
          <h2>{{ r.student.full_name }} <span class="muted small">{{ r.student.email }}</span></h2>
          <span class="row">
            <button v-if="r.is_confirmed" class="btn btn--sm" @click="loadProgress(r.student.id)">Успеваемость</button>
            <span v-else class="badge badge--warning">ждёт подтверждения</span>
            <button class="btn btn--ghost btn--sm" @click="unlink(r.id)">Отвязать</button>
          </span>
        </div>
        <ul v-if="progress[r.student.id]" class="list-plain" style="margin-top: 12px">
          <li v-for="c in progress[r.student.id]" :key="c.course_id" class="stack" style="gap: 6px">
            <div class="row row--between">
              <strong>{{ c.course_title }}</strong>
              <RouterLink :to="{ path: `/progress/courses/${c.course_id}`, query: { student: r.student.id } }" class="small">Подробный отчёт →</RouterLink>
            </div>
            <ProgressBar :value="c.percent_completed" />
            <span class="muted small">пройдено {{ c.percent_completed }}% · средний балл тестов {{ c.average_test_score }}%</span>
          </li>
          <li v-if="!progress[r.student.id].length" class="muted">Ребёнок пока не записан на курсы.</li>
        </ul>
      </section>
    </div>
  </StateBlock>
</template>
