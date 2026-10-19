<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import { submissionsApi } from '@/api/assignments'
import { downloadFile } from '@/api/http'
import AppIcon from '@/components/ui/AppIcon.vue'
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
})
const list = useAsync(() => submissionsApi.list({ status: filters.status || undefined, assignment: filters.assignment }))
const items = computed(() => list.data.value?.results ?? [])
const currentId = ref<number | null>(null)
const current = computed<Submission | null>(() => items.value.find((s) => s.id === currentId.value) ?? items.value[0] ?? null)
const grade = reactive({ score: 0, feedback: '' })

watch(current, (s) => Object.assign(grade, { score: s?.score ?? 0, feedback: s?.feedback ?? '' }), { immediate: true })

function setStatus(status: string) {
  filters.status = status
  currentId.value = null
  list.run()
}

async function save(canResubmit: boolean) {
  const s = current.value
  if (!s) return
  const index = items.value.findIndex((x) => x.id === s.id)
  const ok = await act(() => submissionsApi.grade(s.id, { ...grade, can_resubmit: canResubmit }),
    canResubmit ? 'Возвращено на доработку' : 'Оценка сохранена — ученик получил уведомление')
  if (ok) {
    await list.run()
    // «Принять · следующая»: переходим к следующей работе в очереди
    currentId.value = items.value[Math.min(index, items.value.length - 1)]?.id ?? null
  }
}
</script>

<template>
  <PageHeader title="Проверка работ" subtitle="Домашние задания ваших курсов">
    <button v-if="filters.assignment" class="btn btn--ghost btn--sm" @click="filters.assignment = undefined; list.run()">Все задания ✕</button>
  </PageHeader>

  <div class="pills" style="margin-bottom: var(--space-lg)">
    <button class="pill" :class="{ active: filters.status === 'submitted' }" @click="setStatus('submitted')">Ждут</button>
    <button class="pill" :class="{ active: filters.status === 'returned' }" @click="setStatus('returned')">На доработке</button>
    <button class="pill" :class="{ active: filters.status === 'graded' }" @click="setStatus('graded')">Проверены</button>
    <button class="pill" :class="{ active: !filters.status }" @click="setStatus('')">Все</button>
  </div>

  <StateBlock :loading="list.loading.value && !list.data.value" :error="list.error.value" :empty="!items.length"
              empty-text="Работ нет — всё проверено" @retry="list.run">
    <div class="card card--flush review">
      <aside class="queue">
        <div class="queue__head"><strong>{{ submissionStatusLabels[filters.status] ?? 'Все' }}</strong> <span class="muted">· {{ list.data.value?.total ?? 0 }}</span></div>
        <nav class="side-nav">
          <button v-for="s in items" :key="s.id" :class="{ active: current?.id === s.id }" @click="currentId = s.id">
            <span>{{ s.student_name }} · {{ s.assignment_title }}</span>
          </button>
        </nav>
      </aside>

      <section v-if="current" class="work">
        <div class="row row--between">
          <strong>{{ current.assignment_title }} · {{ current.student_name }}</strong>
          <span class="muted small">сдано {{ fmtDateTime(current.submitted_at) }}<span v-if="current.is_late" class="error"> · с опозданием</span></span>
        </div>
        <div class="work__content">
          <p v-if="current.text_content">{{ current.text_content }}</p>
          <p v-else class="muted">Текстового ответа нет.</p>
          <div class="row">
            <button v-if="current.has_file" class="btn btn--ghost btn--sm" @click="act(() => downloadFile(current!.download_url!, 'работа'))">
              <AppIcon name="download" :size="16" /> Файл ученика
            </button>
            <a v-if="current.file_url" :href="current.file_url" target="_blank" rel="noopener" class="btn btn--ghost btn--sm"><AppIcon name="link" :size="16" /> Ссылка</a>
          </div>
        </div>
        <div class="grade">
          <label class="grade__score">
            <input v-model.number="grade.score" type="number" min="0" step="0.5" aria-label="Балл" />
          </label>
          <input v-model="grade.feedback" placeholder="Комментарий…" class="grade__comment" />
        </div>
        <div class="row" style="justify-content: flex-end">
          <button class="btn btn--ghost" :disabled="busy" @click="save(true)">На доработку</button>
          <button class="btn" :disabled="busy" @click="save(false)">Принять · след. <AppIcon name="arrow-right" :size="16" /></button>
        </div>
      </section>
    </div>
  </StateBlock>
</template>

<style scoped>
.review {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  min-height: 420px;
}
.queue {
  border-right: 1px solid var(--border-default);
  padding: var(--space-md);
  display: grid;
  gap: var(--space-sm);
  align-content: start;
  background: var(--surface-subtle);
}
.queue__head {
  padding: 0 4px;
}
.work {
  padding: var(--space-xl);
  display: grid;
  gap: var(--space-md);
  align-content: start;
}
.work__content {
  display: grid;
  gap: var(--space-sm);
  padding: var(--space-lg);
  border-radius: var(--radius-md);
  background: var(--surface-soft);
  min-height: 160px;
}
.work__content p {
  white-space: pre-line;
  margin: 0;
}
.grade {
  display: grid;
  grid-template-columns: 120px minmax(0, 1fr);
  gap: var(--space-sm);
}
.grade__score input {
  text-align: center;
  font-weight: 600;
}
@media (max-width: 860px) {
  .review {
    grid-template-columns: 1fr;
  }
  .queue {
    border-right: 0;
    border-bottom: 1px solid var(--border-default);
  }
}
</style>
