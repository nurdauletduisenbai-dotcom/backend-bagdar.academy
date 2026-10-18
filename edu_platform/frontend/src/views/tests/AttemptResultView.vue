<script setup lang="ts">
import { computed, reactive } from 'vue'
import { useRouter } from 'vue-router'

import { testsApi } from '@/api/tests'
import AppBadge from '@/components/ui/AppBadge.vue'
import MathText from '@/components/ui/MathText.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAction, useAsync } from '@/composables/useAsync'
import { useAuthStore } from '@/stores/auth'
import type { AttemptResult, ReviewItem } from '@/types/api'
import { attemptStatusLabels, fmtDateTime } from '@/utils/format'

const props = defineProps<{ id: string }>()
const router = useRouter()
const auth = useAuthStore()
const { act, busy } = useAction()
const grades = reactive<Record<number, { score: number; feedback: string }>>({})

const attempt = useAsync(async () => {
  const data = await testsApi.attempt(Number(props.id))
  if ('questions' in data) {
    router.replace(`/tests/${data.test_id}/take`)
    return null
  }
  return data as AttemptResult
})
const result = computed(() => attempt.data.value)

function gradeOf(item: ReviewItem) {
  grades[item.question_id] ??= { score: item.score, feedback: item.teacher_feedback }
  return grades[item.question_id]
}

async function grade(item: ReviewItem) {
  const g = gradeOf(item)
  const updated = await act(() => testsApi.grade(Number(props.id), item.question_id, g.score, g.feedback), 'Оценка сохранена')
  if (updated) attempt.data.value = updated
}

function myAnswer(item: ReviewItem) {
  if (item.text_answer) return item.text_answer
  const textOf = (id: number | string) => item.options.find((o) => o.id === Number(id))?.text ?? `#${id}`
  if (Array.isArray(item.selected_options)) {
    return item.selected_options.map(textOf).join(', ') || '—'
  }
  const pairs = Object.entries(item.selected_options).map(([id, target]) => `${textOf(id)} → ${target}`)
  return pairs.join('; ') || '—'
}
</script>

<template>
  <StateBlock :loading="attempt.loading.value" :error="attempt.error.value" @retry="attempt.run">
    <template v-if="result">
      <PageHeader title="Результат теста" :subtitle="`Сдано ${fmtDateTime(result.submitted_at)}`">
        <template #before><RouterLink :to="`/tests/${result.test_id}/take`" class="small">← К тесту</RouterLink></template>
      </PageHeader>

      <section class="card row" style="gap: 32px; margin-bottom: 16px">
        <div><div class="stat">{{ result.score_pct }}%</div><span class="muted small">{{ result.score }} из {{ result.max_score }} баллов</span></div>
        <div>
          <AppBadge :kind="result.is_passed ? 'success' : 'danger'">{{ result.is_passed ? 'Тест пройден' : 'Не пройден' }}</AppBadge>
          <div class="muted small" style="margin-top: 6px">{{ attemptStatusLabels[result.status] }} · {{ Math.round(result.time_spent_seconds / 60) }} мин</div>
        </div>
      </section>

      <p v-if="result.status === 'submitted'" class="alert alert--warning">
        В тесте есть развёрнутые ответы — итоговый балл появится после проверки учителем.
      </p>

      <div v-if="result.review" class="stack">
        <article v-for="(item, i) in result.review" :key="item.question_id" class="card stack" style="gap: 8px">
          <div class="row row--between">
            <strong>Вопрос {{ i + 1 }}</strong>
            <AppBadge :kind="item.is_correct ? 'success' : item.type === 'open' ? 'info' : 'danger'">
              {{ item.score }} / {{ item.points }}
            </AppBadge>
          </div>
          <MathText :text="item.text" block />
          <div class="small"><span class="muted">Ваш ответ:</span> <MathText :text="myAnswer(item)" /></div>
          <div v-if="item.correct_options.length" class="small">
            <span class="muted">Правильно:</span>
            <span v-for="o in item.correct_options" :key="o.id"> <MathText :text="o.text" /><template v-if="o.match_target"> → {{ o.match_target }}</template>;</span>
          </div>
          <div v-if="item.explanation" class="small"><span class="muted">Разбор:</span> <MathText :text="item.explanation" /></div>
          <div v-if="item.teacher_feedback" class="small"><span class="muted">Комментарий учителя:</span> {{ item.teacher_feedback }}</div>
          <form v-if="auth.isStaff && item.type === 'open'" class="row" @submit.prevent="grade(item)">
            <input v-model.number="gradeOf(item).score" type="number" min="0" :max="item.points" step="0.5" style="width: 90px" />
            <input v-model="gradeOf(item).feedback" placeholder="Комментарий ученику" style="flex: 1; min-width: 200px" />
            <button class="btn btn--sm" :disabled="busy">Оценить</button>
          </form>
        </article>
      </div>
      <p v-else class="muted">Разбор ответов для этого теста скрыт преподавателем.</p>
    </template>
  </StateBlock>
</template>
