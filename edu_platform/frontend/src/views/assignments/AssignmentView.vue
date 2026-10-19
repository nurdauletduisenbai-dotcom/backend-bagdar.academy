<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

import { assignmentsApi } from '@/api/assignments'
import { downloadFile } from '@/api/http'
import AppIcon from '@/components/ui/AppIcon.vue'
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
const dragging = ref(false)

const sub = computed(() => assignment.data.value?.my_submission ?? null)
const canSubmit = computed(() => {
  const a = assignment.data.value
  if (!a || !auth.isStudent) return false
  if (a.is_overdue && !a.accept_late && !sub.value) return false
  return !sub.value || sub.value.status !== 'graded' || sub.value.can_resubmit
})
const statusText = computed(() => (sub.value ? submissionStatusLabels[sub.value.status] : assignment.data.value?.is_overdue ? 'просрочено' : 'не сдано'))

function onDrop(e: DragEvent) {
  dragging.value = false
  file.value = e.dataTransfer?.files?.[0] ?? file.value
}

async function submit() {
  const ok = await act(() => assignmentsApi.submit(Number(props.id), { ...form, file: file.value }), 'Работа отправлена')
  if (ok) {
    file.value = null
    form.text_content = ''
    assignment.run()
  }
}
</script>

<template>
  <StateBlock :loading="assignment.loading.value" :error="assignment.error.value" @retry="assignment.run">
    <template v-if="assignment.data.value">
      <div class="split">
        <section class="stack">
          <RouterLink :to="`/lessons/${assignment.data.value.lesson}`" class="back small muted"><AppIcon name="arrow-left" :size="14" /> К уроку</RouterLink>
          <h1>{{ assignment.data.value.title }}</h1>
          <div class="card">
            <p class="desc">{{ assignment.data.value.description }}</p>
          </div>

          <template v-if="auth.isStudent">
            <div v-if="sub" class="card stack" style="gap: var(--space-xs)">
              <div class="row row--between">
                <h2 style="margin: 0">Моя работа</h2>
                <span class="muted small">сдано {{ fmtDateTime(sub.submitted_at) }}<template v-if="sub.is_late"> · с опозданием</template></span>
              </div>
              <p v-if="sub.text_content" class="desc">{{ sub.text_content }}</p>
              <button v-if="sub.has_file" class="btn btn--text btn--sm" style="justify-self: start"
                      @click="act(() => downloadFile(sub!.download_url!, 'моя работа'))"><AppIcon name="download" :size="16" /> Мой файл</button>
              <a v-if="sub.file_url" :href="sub.file_url" target="_blank" rel="noopener" class="small">{{ sub.file_url }}</a>
            </div>

            <form v-if="canSubmit" class="stack" @submit.prevent="submit">
              <textarea v-model="form.text_content" placeholder="Ваш ответ…" />
              <label class="dropzone" :class="{ over: dragging }" @dragover.prevent="dragging = true" @dragleave="dragging = false" @drop.prevent="onDrop">
                <AppIcon name="upload" />
                <span>{{ file ? file.name : 'Перетащите файл или фото решения — или нажмите, чтобы выбрать' }}</span>
                <input type="file" class="sr-only" @change="file = ($event.target as HTMLInputElement).files?.[0] ?? null" />
              </label>
              <input v-model="form.file_url" type="url" placeholder="…или ссылка (Google Docs, GitHub)" />
            </form>
          </template>
        </section>

        <aside class="card card--subtle side">
          <div><span class="muted small">Дедлайн</span><div class="side__value" :class="{ error: assignment.data.value.is_overdue && !sub }">{{ fmtDateTime(assignment.data.value.deadline) }}</div></div>
          <div class="small">Макс. балл: <strong>{{ assignment.data.value.max_score }}</strong></div>
          <div v-if="auth.isStudent" class="small">Статус: <strong>{{ statusText }}</strong></div>
          <button v-if="canSubmit" class="btn btn--block" :disabled="busy" @click="submit">{{ sub ? 'Отправить заново' : 'Сдать' }}</button>
          <div v-if="sub?.score !== null && sub?.score !== undefined" class="result">
            <div class="stat">{{ sub.score }} <span class="muted small">/ {{ assignment.data.value.max_score }}</span></div>
            <p v-if="sub.feedback" class="small">«{{ sub.feedback }}»</p>
          </div>
          <p v-else-if="auth.isStudent" class="muted small">После проверки здесь появятся балл и комментарий учителя.</p>
          <RouterLink v-if="auth.isTeacher" :to="{ path: '/teach/submissions', query: { assignment: id } }" class="btn btn--block">
            Сдачи ({{ assignment.data.value.submissions_count ?? 0 }})
          </RouterLink>
          <p v-if="assignment.data.value.is_overdue && !assignment.data.value.accept_late" class="small error">Срок прошёл, работы больше не принимаются.</p>
        </aside>
      </div>
    </template>
  </StateBlock>
</template>

<style scoped>
.back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.desc {
  white-space: pre-line;
  margin: 0;
}
.dropzone {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--space-xs);
  cursor: pointer;
  font-weight: 400;
}
.dropzone.over {
  border-color: var(--green-dark);
  background: var(--surface-feature);
}
.sr-only {
  position: absolute;
  width: 1px;
  height: 1px;
  opacity: 0;
  pointer-events: none;
}
.side {
  display: grid;
  gap: var(--space-md);
  position: sticky;
  top: calc(var(--nav-height) + var(--space-md));
}
.side__value {
  font: 500 var(--fs-h4) / 1.3 var(--font-sans);
}
.result {
  padding-top: var(--space-md);
  border-top: 1px solid var(--border-default);
}
.result p {
  margin: var(--space-xs) 0 0;
}
</style>
