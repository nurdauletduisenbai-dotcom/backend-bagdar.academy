<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute } from 'vue-router'

import { submissionsApi } from '@/api/assignments'
import { downloadFile } from '@/api/http'
import AppBadge from '@/components/ui/AppBadge.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppPager from '@/components/ui/AppPager.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAction, useAsync } from '@/composables/useAsync'
import type { Submission } from '@/types/api'
import { fmtDateTime, submissionStatusLabels } from '@/utils/format'

const route = useRoute()
const { act, busy } = useAction()
const filters = reactive({
  status: 'submitted',
  assignment: route.query.assignment ? Number(route.query.assignment) : undefined,
  page: 1,
})
const list = useAsync(() => submissionsApi.list({ status: filters.status || undefined, assignment: filters.assignment, page: filters.page }))
const current = ref<Submission | null>(null)
const grade = reactive({ score: 0, feedback: '', can_resubmit: false })

function openSubmission(s: Submission) {
  current.value = s
  Object.assign(grade, { score: s.score ?? 0, feedback: s.feedback, can_resubmit: false })
}

async function save() {
  if (!current.value) return
  if (await act(() => submissionsApi.grade(current.value!.id, grade), 'Оценка сохранена, ученик получил уведомление')) {
    current.value = null
    list.run()
  }
}
</script>

<template>
  <PageHeader title="Проверка работ" subtitle="Домашние задания ваших курсов" />

  <div class="row" style="margin-bottom: 16px">
    <select v-model="filters.status" style="max-width: 220px" @change="filters.page = 1; list.run()">
      <option value="">Все</option>
      <option value="submitted">Ждут проверки</option>
      <option value="graded">Проверены</option>
      <option value="returned">На доработке</option>
    </select>
    <button v-if="filters.assignment" class="btn btn--ghost btn--sm" @click="filters.assignment = undefined; list.run()">
      Все задания ✕
    </button>
  </div>

  <StateBlock :loading="list.loading.value" :error="list.error.value" :empty="!list.data.value?.results.length"
              empty-text="Работ нет." @retry="list.run">
    <div class="card table-wrap">
      <table class="table">
        <thead><tr><th>Ученик</th><th>Задание</th><th>Сдано</th><th>Статус</th><th>Балл</th><th></th></tr></thead>
        <tbody>
          <tr v-for="s in list.data.value?.results ?? []" :key="s.id">
            <td>{{ s.student_name }}<div class="muted small">{{ s.student_email }}</div></td>
            <td><RouterLink :to="`/assignments/${s.assignment}`">{{ s.assignment_title }}</RouterLink></td>
            <td>{{ fmtDateTime(s.submitted_at) }} <AppBadge v-if="s.is_late" kind="warning">поздно</AppBadge></td>
            <td><AppBadge :kind="s.status === 'graded' ? 'success' : 'warning'">{{ submissionStatusLabels[s.status] }}</AppBadge></td>
            <td>{{ s.score ?? '—' }}</td>
            <td><button class="btn btn--sm" @click="openSubmission(s)">Открыть</button></td>
          </tr>
        </tbody>
      </table>
    </div>
    <AppPager :page="filters.page" :total-pages="list.data.value?.total_pages ?? 1" @change="(p) => { filters.page = p; list.run() }" />
  </StateBlock>

  <AppModal v-if="current" :title="`${current.assignment_title} — ${current.student_name}`" wide @close="current = null">
    <div class="stack">
      <p v-if="current.text_content" style="white-space: pre-line; margin: 0">{{ current.text_content }}</p>
      <div class="row">
        <button v-if="current.has_file" class="btn btn--ghost btn--sm" @click="act(() => downloadFile(current!.download_url!, 'работа'))">Скачать файл</button>
        <a v-if="current.file_url" :href="current.file_url" target="_blank" rel="noopener" class="btn btn--ghost btn--sm">Открыть ссылку</a>
      </div>
      <form class="form" @submit.prevent="save">
        <label>Балл <input v-model.number="grade.score" type="number" min="0" step="0.5" required style="max-width: 120px" /></label>
        <label>Отзыв <textarea v-model="grade.feedback" /></label>
        <label class="inline"><input v-model="grade.can_resubmit" type="checkbox" /> Вернуть на доработку (ученик сможет пересдать)</label>
        <button class="btn" :disabled="busy" style="justify-self: start">Сохранить оценку</button>
      </form>
    </div>
  </AppModal>
</template>
