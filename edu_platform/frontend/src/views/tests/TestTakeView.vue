<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { errorMessage } from '@/api/http'
import { testsApi } from '@/api/tests'
import QuestionInput from '@/components/tests/QuestionInput.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import MathText from '@/components/ui/MathText.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
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
const answers = reactive<Record<number, { selected: number[] | Record<string, string>; text: string }>>({})
const saving = reactive<Record<number, 'saving' | 'saved' | 'error'>>({})
const secondsLeft = ref<number | null>(null)
let timer: ReturnType<typeof setInterval> | null = null
const textTimers: Record<number, ReturnType<typeof setTimeout>> = {}

const answeredCount = computed(
  () => attempt.value?.questions.filter((q) => {
    const a = answers[q.id]
    if (!a) return false
    return a.text.trim() !== '' || (Array.isArray(a.selected) ? a.selected.length > 0 : Object.keys(a.selected).length > 0)
  }).length ?? 0,
)

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
  if (!auto && !confirm(`Отправить тест? Отвечено ${answeredCount.value} из ${attempt.value.questions.length}.`)) return
  Object.values(textTimers).forEach(clearTimeout)
  // Дожидаемся сохранения текстовых ответов, введённых в последние секунды
  await Promise.all(attempt.value.questions.filter((q) => ['short', 'number', 'open'].includes(q.type)).map(save))
  const result = await act(() => testsApi.submit(attempt.value!.attempt_id))
  stopTimer()
  unwatchCheating()
  if (result) router.push(`/attempts/${result.attempt_id}`)
}

// ---------- Античит: фиксируем уход со вкладки и копирование ----------
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
      <PageHeader :title="info.data.value.title" :subtitle="testModeLabels[info.data.value.mode]">
        <template #before>
          <RouterLink :to="`/courses/${info.data.value.course}`" class="small">← К курсу</RouterLink>
        </template>
        <RouterLink v-if="auth.isStaff" :to="`/teach/tests/${id}`" class="btn btn--ghost">Редактор теста</RouterLink>
      </PageHeader>

      <!-- Вступление -->
      <section v-if="!attempt" class="grid--2" style="align-items: start">
        <div class="card stack">
          <p v-if="info.data.value.description" style="margin: 0">{{ info.data.value.description }}</p>
          <ul class="small" style="margin: 0; padding-left: 18px">
            <li>Вопросов: {{ info.data.value.questions_count }}</li>
            <li>Время: {{ info.data.value.time_limit_minutes ? `${info.data.value.time_limit_minutes} мин` : 'без ограничения' }}</li>
            <li>Проходной балл: {{ info.data.value.passing_score_pct }}%</li>
            <li>Попыток: {{ info.data.value.attempts_used }} из {{ info.data.value.max_attempts || '∞' }}</li>
          </ul>
          <p class="muted small" style="margin: 0">
            Ответы сохраняются автоматически. Уход со вкладки и копирование фиксируются.
          </p>
          <button class="btn" :disabled="busy" style="justify-self: start" @click="start">Начать / продолжить</button>
        </div>
        <div class="card">
          <h2>Мои попытки</h2>
          <StateBlock :loading="attempts.loading.value" :error="attempts.error.value"
                      :empty="!attempts.data.value?.length" empty-text="Попыток ещё не было." @retry="attempts.run">
            <ul class="list-plain">
              <li v-for="a in attempts.data.value ?? []" :key="a.id" class="row row--between">
                <RouterLink :to="`/attempts/${a.id}`">{{ fmtDateTime(a.started_at) }}</RouterLink>
                <span class="row small">
                  <span v-if="a.status !== 'in_progress'">{{ a.score_pct }}%</span>
                  <AppBadge :kind="a.is_passed ? 'success' : 'default'">{{ attemptStatusLabels[a.status] }}</AppBadge>
                </span>
              </li>
            </ul>
          </StateBlock>
        </div>
      </section>

      <!-- Прохождение -->
      <section v-else class="stack">
        <div class="card row row--between sticky">
          <span>Отвечено {{ answeredCount }} из {{ attempt.questions.length }}</span>
          <strong v-if="timeText" :class="{ error: (secondsLeft ?? 0) < 60 }">⏱ {{ timeText }}</strong>
          <button class="btn" :disabled="busy" @click="submit()">Сдать тест</button>
        </div>

        <article v-for="q in attempt.questions" :key="q.id" class="card stack">
          <div class="row row--between">
            <strong>Вопрос {{ q.order }}</strong>
            <span class="muted small">
              {{ q.points }} б.
              <template v-if="saving[q.id] === 'saving'"> · сохраняем…</template>
              <template v-else-if="saving[q.id] === 'saved'"> · сохранено</template>
              <span v-else-if="saving[q.id] === 'error'" class="error"> · ошибка</span>
            </span>
          </div>
          <MathText :text="q.text" block />
          <QuestionInput :question="q" :selected="answers[q.id].selected" :text="answers[q.id].text"
                         @update:selected="onSelected(q, $event)" @update:text="onText(q, $event)" />
        </article>

        <button class="btn" :disabled="busy" style="justify-self: start" @click="submit()">Сдать тест</button>
      </section>
    </template>
  </StateBlock>
</template>

<style scoped>
.sticky {
  position: sticky;
  top: 64px;
  z-index: 5;
}
</style>
