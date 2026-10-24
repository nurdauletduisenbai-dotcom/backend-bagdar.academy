<script setup lang="ts">
import { computed, reactive } from 'vue'
import { useRouter } from 'vue-router'

import { testsApi } from '@/api/tests'
import AppIcon from '@/components/ui/AppIcon.vue'
import MathText from '@/components/ui/MathText.vue'
import ProgressRing from '@/components/ui/ProgressRing.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAction, useAsync } from '@/composables/useAsync'
import { useAuthStore } from '@/stores/auth'
import type { AttemptResult, ReviewItem, TestInfo } from '@/types/api'
import { attemptStatusLabels, fmtDateTime } from '@/utils/format'

const props = defineProps<{ id: string }>()
const router = useRouter()
const auth = useAuthStore()
const { act, busy } = useAction()
const grades = reactive<Record<number, { score: number; feedback: string }>>({})
let test: TestInfo | null = null

const attempt = useAsync(async () => {
  const data = await testsApi.attempt(Number(props.id))
  if ('questions' in data) {
    router.replace(`/tests/${data.test_id}/take`)
    return null
  }
  test = await testsApi.get(data.test_id).catch(() => null)
  return data as AttemptResult
})
const result = computed(() => attempt.data.value)
const testInfo = computed(() => (attempt.data.value ? test : null))

function stateOf(item: ReviewItem): 'ok' | 'wrong' | 'pending' {
  if (item.type === 'open' && !item.teacher_feedback && item.score === 0) return 'pending'
  return item.is_correct || (item.type === 'open' && item.score > 0) ? 'ok' : 'wrong'
}

function myAnswer(item: ReviewItem) {
  if (item.text_answer) return item.text_answer
  const textOf = (id: number | string) => item.options.find((o) => o.id === Number(id))?.text ?? `#${id}`
  if (Array.isArray(item.selected_options)) return item.selected_options.map(textOf).join(', ') || '—'
  return Object.entries(item.selected_options).map(([id, t]) => `${textOf(id)} → ${t}`).join('; ') || '—'
}

function gradeOf(item: ReviewItem) {
  grades[item.question_id] ??= { score: item.score, feedback: item.teacher_feedback }
  return grades[item.question_id]
}

async function grade(item: ReviewItem) {
  const g = gradeOf(item)
  const updated = await act(() => testsApi.grade(Number(props.id), item.question_id, g.score, g.feedback), 'Оценка сохранена')
  if (updated) attempt.data.value = updated
}
</script>

<template>
  <StateBlock :loading="attempt.loading.value" :error="attempt.error.value" @retry="attempt.run">
    <template v-if="result">
      <!-- Итог (вайрфрейм 2j) -->
      <section class="band page-band summary">
        <ProgressRing :value="result.score_pct" :size="120" dark :label="`${Math.round(result.score_pct)}%`" />
        <div class="summary__body">
          <div class="eyebrow">{{ result.status === 'submitted' ? 'Ждёт проверки учителя' : result.is_passed ? 'Тест сдан' : 'Тест не сдан' }}</div>
          <h1 class="summary__title">{{ testInfo?.title ?? 'Тест' }} · {{ result.score }} из {{ result.max_score }} б.</h1>
          <p class="muted">{{ Math.round(result.time_spent_seconds / 60) }} мин · {{ attemptStatusLabels[result.status] }} · {{ fmtDateTime(result.submitted_at) }}</p>
        </div>
      </section>

      <div v-if="result.review" class="strip" aria-hidden="true">
        <span v-for="item in result.review" :key="item.question_id" :class="`strip--${stateOf(item)}`" />
      </div>

      <div v-if="result.review" class="stack">
        <article v-for="(item, i) in result.review" :key="item.question_id" class="card review" :class="`review--${stateOf(item)}`">
          <div class="row row--between">
            <strong>Вопрос {{ i + 1 }} · {{ item.score }}/{{ item.points }}</strong>
            <span v-if="stateOf(item) === 'pending'" class="badge badge--warning">ждёт проверки учителем</span>
            <span v-else-if="stateOf(item) === 'ok'" class="badge badge--success"><AppIcon name="check" :size="12" /> верно</span>
            <span v-else class="badge badge--danger">неверно</span>
          </div>
          <MathText :text="item.text" block />
          <div class="small"><span class="muted">Ваш ответ:</span> <MathText :text="myAnswer(item)" /></div>
          <div v-if="item.correct_options.length" class="small">
            <span class="muted">Верно:</span>
            <span v-for="o in item.correct_options" :key="o.id"> <MathText :text="o.text" /><template v-if="o.match_target"> → {{ o.match_target }}</template>;</span>
          </div>
          <div v-if="item.explanation" class="small explain"><span class="muted">Разбор:</span> <MathText :text="item.explanation" /></div>
          <div v-if="item.teacher_feedback" class="small"><span class="muted">Комментарий учителя:</span> {{ item.teacher_feedback }}</div>
          <form v-if="auth.isStaff && item.type === 'open'" class="row" @submit.prevent="grade(item)">
            <input v-model.number="gradeOf(item).score" type="number" min="0" :max="item.points" step="0.5" style="width: 100px" />
            <input v-model="gradeOf(item).feedback" placeholder="Комментарий ученику" style="flex: 1; min-width: 200px" />
            <button class="btn btn--sm" :disabled="busy">Оценить</button>
          </form>
        </article>
      </div>
      <p v-else class="muted">Разбор ответов для этого теста скрыт преподавателем.</p>

      <div class="row actions">
        <RouterLink :to="`/tests/${result.test_id}/take`" class="btn">Пройти ещё раз</RouterLink>
        <RouterLink v-if="testInfo" :to="`/courses/${testInfo.course}`" class="btn btn--ghost">К курсу</RouterLink>
      </div>
    </template>
  </StateBlock>
</template>

<style scoped>
.summary {
  display: flex;
  align-items: center;
  gap: var(--space-xl);
  flex-wrap: wrap;
}
.summary__body {
  display: grid;
  gap: var(--space-xs);
}
.summary__body p {
  margin: 0;
}
.summary__title {
  font: 500 var(--fs-h3) / var(--lh-h3) var(--font-sans);
}
.strip {
  display: flex;
  gap: 6px;
  margin-bottom: var(--space-lg);
}
.strip span {
  flex: 1;
  height: 8px;
  border-radius: var(--radius-full);
}
.strip--ok {
  background: var(--green-500);
}
.strip--wrong {
  background: var(--error-text);
}
.strip--pending {
  background: #e3a33a;
}
.review {
  display: grid;
  gap: var(--space-xs);
}
.review--wrong {
  border-color: #f0b8b3;
}
.review--pending {
  border-color: #f2d49b;
}
.explain {
  padding: var(--space-xs) var(--space-sm);
  background: var(--surface-subtle);
  border-radius: var(--radius-sm);
}
.actions {
  margin-top: var(--space-xl);
}
</style>
