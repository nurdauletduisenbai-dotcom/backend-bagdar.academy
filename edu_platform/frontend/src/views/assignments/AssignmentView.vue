<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

import { assignmentsApi } from '@/api/assignments'
import { downloadFile } from '@/api/http'
import AppBadge from '@/components/ui/AppBadge.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAction, useAsync } from '@/composables/useAsync'
import { useAuthStore } from '@/stores/auth'
import { fmtDateTime, submissionStatusLabels } from '@/utils/format'

const props = defineProps<{ id: string }>()
const auth = useAuthStore()
const { act, busy } = useAction()
const assignment = useAsync(() => assignmentsApi.get(Number(props.id)))
const form = reactive({ text_content: '', file_url: '' })
const file = ref<File | null>(null)

const sub = computed(() => assignment.data.value?.my_submission ?? null)
const canSubmit = computed(() => {
  const a = assignment.data.value
  if (!a || !auth.isStudent) return false
  if (a.is_overdue && !a.accept_late && !sub.value) return false
  return !sub.value || sub.value.status !== 'graded' || sub.value.can_resubmit
})

async function submit() {
  const ok = await act(() => assignmentsApi.submit(Number(props.id), { ...form, file: file.value }), 'Работа отправлена')
  if (ok) {
    file.value = null
    assignment.run()
  }
}
</script>

<template>
  <StateBlock :loading="assignment.loading.value" :error="assignment.error.value" @retry="assignment.run">
    <template v-if="assignment.data.value">
      <PageHeader :title="assignment.data.value.title" :subtitle="`Дедлайн: ${fmtDateTime(assignment.data.value.deadline)} · макс. ${assignment.data.value.max_score} баллов`">
        <template #before>
          <RouterLink :to="`/lessons/${assignment.data.value.lesson}`" class="small">← К уроку</RouterLink>
        </template>
        <RouterLink v-if="auth.isTeacher" :to="{ path: '/teach/submissions', query: { assignment: id } }" class="btn btn--ghost">
          Сдачи ({{ assignment.data.value.submissions_count ?? 0 }})
        </RouterLink>
      </PageHeader>

      <div class="grid--2" style="align-items: start">
        <section class="card">
          <h2>Задание</h2>
          <p style="white-space: pre-line; margin: 0">{{ assignment.data.value.description }}</p>
          <p v-if="assignment.data.value.is_overdue" class="small" :class="assignment.data.value.accept_late ? 'muted' : 'error'">
            Срок прошёл. {{ assignment.data.value.accept_late ? 'Работа будет помечена как сданная с опозданием.' : 'Работы больше не принимаются.' }}
          </p>
        </section>

        <section v-if="auth.isStudent" class="card stack">
          <h2>Моя работа</h2>
          <template v-if="sub">
            <div class="row">
              <AppBadge :kind="sub.status === 'graded' ? 'success' : 'warning'">{{ submissionStatusLabels[sub.status] }}</AppBadge>
              <AppBadge v-if="sub.is_late" kind="warning">с опозданием</AppBadge>
              <span class="muted small">{{ fmtDateTime(sub.submitted_at) }}</span>
            </div>
            <p v-if="sub.text_content" style="white-space: pre-line; margin: 0">{{ sub.text_content }}</p>
            <button v-if="sub.has_file" class="btn btn--ghost btn--sm" style="justify-self: start"
                    @click="act(() => downloadFile(sub!.download_url!, 'моя работа'))">Скачать мой файл</button>
            <div v-if="sub.score !== null" class="alert alert--success">
              <span>Оценка: <strong>{{ sub.score }}</strong> / {{ assignment.data.value.max_score }}</span>
              <span v-if="sub.feedback">«{{ sub.feedback }}»</span>
            </div>
          </template>

          <form v-if="canSubmit" class="form" @submit.prevent="submit">
            <label>Ответ <textarea v-model="form.text_content" /></label>
            <label>Файл <input type="file" @change="file = ($event.target as HTMLInputElement).files?.[0] ?? null" /></label>
            <label>…или ссылка (Google Docs, GitHub) <input v-model="form.file_url" type="url" /></label>
            <button class="btn" :disabled="busy" style="justify-self: start">{{ sub ? 'Отправить заново' : 'Сдать работу' }}</button>
          </form>
          <p v-else-if="sub?.status === 'graded'" class="muted small">Работа проверена. Пересдать можно, если учитель вернёт её на доработку.</p>
        </section>
      </div>
    </template>
  </StateBlock>
</template>
