<script setup lang="ts">
import { reactive } from 'vue'

import { coursesApi, groupsApi } from '@/api/courses'
import { progressApi } from '@/api/progress'
import ProgressBar from '@/components/ui/ProgressBar.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAction, useAsync } from '@/composables/useAsync'
import { useAuthStore } from '@/stores/auth'
import { enrollmentStatusLabels } from '@/utils/format'

const props = defineProps<{ courseId: number }>()
const auth = useAuthStore()
const { act, busy } = useAction()
const table = useAsync(() => progressApi.courseStudents(props.courseId))
const groups = useAsync(() => groupsApi.list(props.courseId))
const form = reactive({ student_email: '', access_days: 365, group_id: null as number | null })

async function enroll() {
  if (await act(() => coursesApi.enrollStudent(props.courseId, form), 'Ученик записан')) {
    form.student_email = ''
    table.run()
  }
}
</script>

<template>
  <div class="stack">
    <section v-if="auth.isStaff" class="card">
      <h2>Записать ученика</h2>
      <form class="row" @submit.prevent="enroll">
        <input v-model="form.student_email" type="email" placeholder="email ученика школы" style="max-width: 260px" required />
        <select v-model="form.group_id" style="max-width: 200px">
          <option :value="null">Без группы</option>
          <option v-for="g in groups.data.value ?? []" :key="g.id" :value="g.id">{{ g.name }}</option>
        </select>
        <input v-model.number="form.access_days" type="number" min="1" style="max-width: 110px" title="Дней доступа" />
        <button class="btn" :disabled="busy">Записать</button>
      </form>
      <p class="muted small">Ученик должен состоять в школе. Новых учеников приглашают в разделе «Приглашения».</p>
    </section>

    <section class="card">
      <h2>Прогресс учеников</h2>
      <StateBlock :loading="table.loading.value" :error="table.error.value" :empty="!table.data.value?.length"
                  empty-text="На курс ещё никто не записан." @retry="table.run">
        <div class="table-wrap">
          <table class="table">
            <thead><tr><th>Ученик</th><th>Группа</th><th>Запись</th><th style="width: 180px">Пройдено</th><th>Ср. балл</th><th></th></tr></thead>
            <tbody>
              <tr v-for="r in table.data.value ?? []" :key="r.student_id">
                <td>{{ r.student_name }}<div class="muted small">{{ r.student_email }}</div></td>
                <td>{{ r.group ?? '—' }}</td>
                <td>{{ enrollmentStatusLabels[r.enrollment_status] }}</td>
                <td><ProgressBar :value="r.percent_completed" /> <span class="small">{{ r.percent_completed }}%</span></td>
                <td>{{ r.average_test_score }}%</td>
                <td><RouterLink :to="{ path: `/progress/courses/${courseId}`, query: { student: r.student_id } }" class="btn btn--ghost btn--sm">Отчёт</RouterLink></td>
              </tr>
            </tbody>
          </table>
        </div>
      </StateBlock>
    </section>
  </div>
</template>
