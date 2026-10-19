<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { errorMessage } from '@/api/http'
import { testsApi } from '@/api/tests'
import QuestionInput from '@/components/tests/QuestionInput.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import MathText from '@/components/ui/MathText.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAction, useAsync } from '@/composables/useAsync'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/stores/toast'
import type { AttemptQuestion, AttemptStarted } from '@/types/api'
import { attemptStatusLabels, fmtDateTime, testModeLabels } from '@/utils/format'

const props = defineProps<{ id: string }>()
const router = useRouter()
const auth = useAuthStore()
const toast = useToast()
const { act, busy } = useAction()

const info = useAsync(() => testsApi.get(Number(props.id)))
const attempts = useAsync(() => testsApi.attempts(Number(props.id)))

const attempt = ref<AttemptStarted | null>(null)
const current = ref(0)
const answers = reactive<Record<number, { selected: number[] | Record<string, string>; text: string }>>({})
const saving = reactive<Record<number, 'saving' | 'saved' | 'error'>>({})
const secondsLeft = ref<number | null>(null)
let timer: ReturnType<typeof setInterval> | null = null
const textTimers: Record<number, ReturnType<typeof setTimeout>> = {}

const question = computed(() => attempt.value?.questions[current.value] ?? null)
const isAnswered = (q: AttemptQuestion) => {
  const a = answers[q.id]
  if (!a) return false
  return a.text.trim() !== '' || (Array.isArray(a.selected) ? a.selected.length > 0 : Object.keys(a.selected).length > 0)
}
const answeredCount = computed(() => attempt.value?.questions.filter(isAnswered).length ?? 0)
const timeText = computed(() => {
  if (secondsLeft.value === null) return ''
  const s = Math.max(0, secondsLeft.value)
  return `${Math.floor(s / 60)}:${String(s % 60).padStart(2, '0')}`
})

async function start() {
  const data = await act(() => testsApi.start(Number(props.id)))
  if (!data) return
  attempt.value = data
  for (const q of data.questions) {
    answers[q.id] = {
      selected: q.saved_answer?.selected_options ?? (q.type === 'match' ? {} : []),
      text: q.saved_answer?.text_answer ?? '',
    }
  }
  const firstEmpty = data.questions.findIndex((q) => !isAnswered(q))
  current.value = firstEmpty >= 0 ? firstEmpty : 0
  startTimer()
  watchCheating()
}

function startTimer() {
  if (!attempt.value?.deadline) return
  const deadline = new Date(attempt.value.deadline).getTime()
  const tick = () => {
    secondsLeft.value = Math.round((deadline - Date.now()) / 1000)
    if (secondsLeft.value <= 0) {
      stopTimer()
      toast.info('Время вышло — тест отправлен автоматически')
      submit(true)
    }
  }
  tick()
  timer = setInterval(tick, 1000)
}

function stopTimer() {
  if (timer) clearInterval(timer)
  timer = null
}

async function save(q: AttemptQuestion) {
  if (!attempt.value) return
  const a = answers[q.id]
  saving[q.id] = 'saving'
  try {
    const usesText = ['short', 'number', 'open'].includes(q.type)
    await testsApi.saveAnswer(attempt.value.attempt_id, q.id,
      usesText ? { text_answer: a.text } : { selected_options: a.selected })
    saving[q.id] = 'saved'
  } catch (e) {
    saving[q.id] = 'error'
    toast.error(errorMessage(e))
  }
}

function onSelected(q: AttemptQuestion, value: number[] | Record<string, string>) {
  answers[q.id].selected = value
  save(q)
}

function onText(q: AttemptQuestion, value: string) {
  answers[q.id].text = value
  clearTimeout(textTimers[q.id])
  textTimers[q.id] = setTimeout(() => save(q), 700)
}

async function submit(auto = false) {
  if (!attempt.value) return
  if (!auto && !confirm(`Сдать тест? Отвечено ${answeredCount.value} из ${attempt.value.questions.length}.`)) return
  Object.values(textTimers).forEach(clearTimeout)
  await Promise.all(attempt.value.questions.filter((q) => ['short', 'number', 'open'].includes(q.type)).map(save))
  const result = await act(() => testsApi.submit(attempt.value!.attempt_id))
  stopTimer()
  unwatchCheating()
  if (result) router.push(`/attempts/${result.attempt_id}`)
}

// ---------- Античит: уход со вкладки и копирование ----------
function logEvent(type: string) {
  if (attempt.value) testsApi.logEvent(attempt.value.attempt_id, type).catch(() => {})
}
const onVisibility = () => document.visibilityState === 'hidden' && logEvent('tab_blur')
const onCopy = () => logEvent('copy_paste')
function watchCheating() {
  document.addEventListener('visibilitychange', onVisibility)
  document.addEventListener('copy', onCopy)
  document.addEventListener('paste', onCopy)
}
function unwatchCheating() {
  document.removeEventListener('visibilitychange', onVisibility)
  document.removeEventListener('copy', onCopy)
  document.removeEventListener('paste', onCopy)
}

onBeforeUnmount(() => {
  stopTimer()
  unwatchCheating()
})
</script>

<template>
  <StateBlock :loading="info.loading.value" :error="info.error.value" @retry="info.run">
    <template v-if="info.data.value">
      <!-- ====== Вступление (вайрфрейм 1i) ====== -->
      <template v-if="!attempt">
        <section class="band page-band intro">
          <RouterLink :to="`/courses/${info.data.value.course}`" class="back small"><AppIcon name="arrow-left" :size="14" /> К курсу</RouterLink>
          <div class="eyebrow">{{ testModeLabels[info.data.value.mode] }}</div>
          <h1 class="intro__title">{{ info.data.value.title }}</h1>
          <p v-if="info.data.value.description" class="muted">{{ info.data.value.description }}</p>
          <div class="intro__stats">
            <span><strong>{{ info.data.value.questions_count }}</strong> вопросов</span>
            <span><strong>{{ info.data.value.time_limit_minutes || '∞' }}</strong> мин</span>
            <span><strong>{{ info.data.value.passing_score_pct }}%</strong> проход</span>
            <span><strong>{{ info.data.value.attempts_used }}/{{ info.data.value.max_attempts || '∞' }}</strong> попытки</span>
          </div>
          <div class="row">
            <button class="btn btn--lg" :disabled="busy" @click="start">Начать тест</button>
            <RouterLink v-if="auth.isStaff" :to="`/teach/tests/${id}`" class="btn btn--ghost">Редактор теста</RouterLink>
          </div>
        </section>

        <div class="alert">
          <span class="row"><AppIcon name="info" :size="16" /> Ответы сохраняются автоматически. Уход со вкладки и копирование фиксируются.</span>
        </div>

        <section class="attempts">
          <h2>Мои попытки</h2>
          <StateBlock :loading="attempts.loading.value" :error="attempts.error.value"
                      :empty="!attempts.data.value?.length" empty-text="Попыток ещё не было" @retry="attempts.run">
            <ul class="list-lines">
              <li v-for="a in attempts.data.value ?? []" :key="a.id" class="row row--between">
                <RouterLink :to="`/attempts/${a.id}`">{{ fmtDateTime(a.started_at) }}</RouterLink>
                <span class="row small">
                  <span v-if="a.status !== 'in_progress'">{{ a.score_pct }}%</span>
                  <span class="badge" :class="a.is_passed ? 'badge--success' : a.status === 'submitted' ? 'badge--warning' : ''">
                    {{ a.is_passed ? 'сдан' : attemptStatusLabels[a.status] }}
                  </span>
                </span>
              </li>
            </ul>
          </StateBlock>
        </section>
      </template>

      <!-- ====== Прохождение: один вопрос на экран + навигатор (1g + 1h) ====== -->
      <template v-else-if="question">
        <div class="take-head">
          <span class="row"><AppIcon name="x" :size="16" /> <strong>{{ attempt.title }}</strong>
            <span class="muted small">· {{ testModeLabels[info.data.value.mode] }}</span></span>
          <span v-if="timeText" class="timer" :class="{ urgent: (secondsLeft ?? 0) < 60 }"><AppIcon name="clock" :size="14" /> {{ timeText }}</span>
        </div>
        <div class="take-progress"><div :style="{ width: `${((current + 1) / attempt.questions.length) * 100}%` }" /></div>

        <div class="split">
          <article class="card question">
            <div class="eyebrow">Вопрос {{ current + 1 }} из {{ attempt.questions.length }} · {{ question.points }} б.</div>
            <MathText :text="question.text" block class="question__text" />
            <QuestionInput :key="question.id" :question="question" :selected="answers[question.id].selected"
                           :text="answers[question.id].text"
                           @update:selected="onSelected(question, $event)" @update:text="onText(question, $event)" />
            <div class="question__nav">
              <button class="btn btn--text" :disabled="current === 0" @click="current--"><AppIcon name="arrow-left" :size="16" /> Назад</button>
              <span class="muted small">
                <template v-if="saving[question.id] === 'saving'">сохраняем…</template>
                <template v-else-if="saving[question.id] === 'saved'">сохранено</template>
                <span v-else-if="saving[question.id] === 'error'" class="error">ошибка сохранения</span>
              </span>
              <button v-if="current < attempt.questions.length - 1" class="btn" @click="current++">Дальше <AppIcon name="arrow-right" :size="16" /></button>
              <button v-else class="btn" :disabled="busy" @click="submit()">Сдать тест</button>
            </div>
          </article>

          <aside class="card navigator">
            <span class="muted small">Отвечено {{ answeredCount }} / {{ attempt.questions.length }}</span>
            <div class="navigator__grid">
              <button v-for="(q, i) in attempt.questions" :key="q.id" class="nav-chip"
                      :class="{ current: i === current, answered: isAnswered(q) }" @click="current = i">{{ i + 1 }}</button>
            </div>
            <button class="btn btn--block" :disabled="busy" @click="submit()">Сдать тест</button>
          </aside>
        </div>
      </template>
    </template>
  </StateBlock>
</template>

<style scoped>
.back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  color: var(--text-on-dark-muted);
}
.intro {
  display: grid;
  gap: var(--space-sm);
  justify-items: start;
}
.intro p {
  margin: 0;
}
.intro__title {
  font: 500 var(--fs-h2) / var(--lh-h2) var(--font-sans);
  letter-spacing: -0.5px;
}
.intro__stats {
  display: flex;
  gap: var(--space-xl);
  flex-wrap: wrap;
  color: var(--text-on-dark-muted);
  margin: var(--space-xs) 0;
}
.intro__stats strong {
  font: 500 var(--fs-h4) / 1 var(--font-sans);
  color: var(--text-on-dark);
  margin-right: 4px;
}
.attempts {
  margin-top: var(--space-xl);
}
.take-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-md);
}
.timer {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: var(--radius-full);
  border: 1px solid var(--border-strong);
  font: 600 var(--fs-body-sm) / 1 var(--font-sans);
  font-variant-numeric: tabular-nums;
}
.timer.urgent {
  border-color: var(--error-text);
  color: var(--error-text);
}
.take-progress {
  height: 4px;
  background: var(--hairline-soft);
  border-radius: var(--radius-full);
  margin: var(--space-md) 0 var(--space-xl);
  overflow: hidden;
}
.take-progress div {
  height: 100%;
  background: var(--green-500);
  transition: width var(--dur-base) var(--ease-standard);
}
.question {
  display: grid;
  gap: var(--space-lg);
}
.question__text {
  font: 500 var(--fs-h4) / var(--lh-h4) var(--font-sans);
  color: var(--text-strong);
}
.question__nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-sm);
  padding-top: var(--space-md);
  border-top: 1px solid var(--border-soft);
}
.navigator {
  display: grid;
  gap: var(--space-md);
  position: sticky;
  top: calc(var(--nav-height) + var(--space-md));
}
.navigator__grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 6px;
}
.nav-chip {
  height: 36px;
  border-radius: var(--radius-sm);
  border: 1px solid var(--border-strong);
  background: var(--canvas);
  font: 600 var(--fs-caption) / 1 var(--font-sans);
  cursor: pointer;
  color: var(--text-strong);
}
.nav-chip.answered {
  background: var(--ink);
  border-color: var(--ink);
  color: var(--text-on-dark);
}
.nav-chip.current {
  background: var(--green-500);
  border-color: var(--green-500);
  color: var(--teal-900);
}
</style>
