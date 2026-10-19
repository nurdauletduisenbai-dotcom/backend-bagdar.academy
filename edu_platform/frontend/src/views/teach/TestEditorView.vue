<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { questionsApi, testsApi } from '@/api/tests'
import AppBadge from '@/components/ui/AppBadge.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppModal from '@/components/ui/AppModal.vue'
import MathText from '@/components/ui/MathText.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAction, useAsync } from '@/composables/useAsync'
import type { TestInfo } from '@/types/api'
import { attemptStatusLabels, fmtDateTime, fromLocalInput, questionTypeLabels, testModeLabels, toLocalInput } from '@/utils/format'

const props = defineProps<{ id: string }>()
const testId = Number(props.id)
const router = useRouter()
const { act, busy } = useAction()
const tab = ref<'questions' | 'settings' | 'stats' | 'attempts'>('questions')

const form = reactive<Partial<TestInfo>>({})
const test = useAsync(async () => {
  const t = await testsApi.get(testId)
  Object.assign(form, { ...t, available_from: toLocalInput(t.available_from), available_to: toLocalInput(t.available_to) })
  return t
})
const items = useAsync(() => testsApi.questions(testId))
const stats = useAsync(() => testsApi.stats(testId), { immediate: false })
const attempts = useAsync(() => testsApi.attempts(testId), { immediate: false })

const picking = ref(false)
const bankSearch = ref('')
const bank = useAsync(() => questionsApi.list({ search: bankSearch.value || undefined, is_archived: false }), { immediate: false })

function open(next: typeof tab.value) {
  tab.value = next
  if (next === 'stats') stats.run()
  if (next === 'attempts') attempts.run()
}

async function saveSettings() {
  const payload = { ...form, available_from: fromLocalInput(form.available_from ?? ''), available_to: fromLocalInput(form.available_to ?? '') }
  if (await act(() => testsApi.update(testId, payload), 'Тест сохранён')) test.run()
}

async function removeTest() {
  if (!confirm('Удалить тест вместе с попытками?')) return
  const courseId = test.data.value?.course
  if (await act(() => testsApi.remove(testId), 'Тест удалён')) router.push(`/teach/courses/${courseId}`)
}

function openBank() {
  picking.value = true
  bank.run()
}

async function add(questionId: number) {
  if (await act(() => testsApi.addQuestion(testId, questionId, 1), 'Вопрос добавлен')) {
    items.run()
    test.run()
  }
}

async function setPoints(questionId: number, points: number) {
  await act(() => testsApi.updateQuestion(testId, questionId, { points }))
  items.run()
}

async function removeQuestion(questionId: number) {
  if (await act(() => testsApi.removeQuestion(testId, questionId), 'Убрано из теста')) items.run()
}

const inTest = (questionId: number) => items.data.value?.some((i) => i.question.id === questionId)
</script>

<template>
  <StateBlock :loading="test.loading.value && !test.data.value" :error="test.error.value" @retry="test.run">
    <template v-if="test.data.value">
      <PageHeader :title="test.data.value.title" :subtitle="`${testModeLabels[test.data.value.mode]} · ${test.data.value.questions_count} вопросов`">
        <template #before><RouterLink :to="`/teach/courses/${test.data.value.course}`" class="small">← Редактор курса</RouterLink></template>
        <RouterLink :to="`/tests/${id}/take`" class="btn btn--ghost">Страница теста</RouterLink>
      </PageHeader>

      <div class="tabs">
        <button :class="{ active: tab === 'questions' }" @click="open('questions')">Вопросы</button>
        <button :class="{ active: tab === 'settings' }" @click="open('settings')">Настройки</button>
        <button :class="{ active: tab === 'stats' }" @click="open('stats')">Статистика</button>
        <button :class="{ active: tab === 'attempts' }" @click="open('attempts')">Попытки и проверка</button>
      </div>

      <div v-if="tab === 'questions'" class="split">
        <section class="card">
          <div class="row row--between">
            <h2>Вопросы · {{ items.data.value?.length ?? 0 }}</h2>
            <button class="btn btn--sm" @click="openBank">+ из банка</button>
          </div>
          <StateBlock :loading="items.loading.value" :error="items.error.value" :empty="!items.data.value?.length"
                      empty-text="Добавьте вопросы из банка. Новые вопросы создаются в «Банке вопросов»." @retry="items.run">
            <ul class="list-plain">
              <li v-for="(item, i) in items.data.value ?? []" :key="item.id" class="tq">
                <span class="tq__handle muted">⠿</span>
                <span class="tq__text">{{ i + 1 }}. <MathText :text="item.question.text" /> <span class="badge">{{ questionTypeLabels[item.question.type] }}</span></span>
                <input type="number" min="0" step="0.5" :value="item.points" class="tq__points" title="Баллы"
                       @change="setPoints(item.question.id, Number(($event.target as HTMLInputElement).value))" />
                <span class="small muted">б.</span>
                <button class="btn btn--text btn--sm" title="Убрать" @click="removeQuestion(item.question.id)"><AppIcon name="x" :size="14" /></button>
              </li>
            </ul>
          </StateBlock>
          <button class="dropzone add-q" @click="openBank">+ из банка · <RouterLink to="/teach/questions" @click.stop>+ новый</RouterLink></button>
          <p class="muted small">После первой сданной попытки состав теста заблокирован — для правок создайте новый тест.</p>
        </section>
        <aside class="card card--subtle summary">
          <div>Режим: <strong>{{ testModeLabels[test.data.value.mode] }}</strong></div>
          <div>Время: <strong>{{ test.data.value.time_limit_minutes ? `${test.data.value.time_limit_minutes} мин` : 'без таймера' }}</strong></div>
          <div>Проход: <strong>{{ test.data.value.passing_score_pct }}%</strong></div>
          <div>Попыток: <strong>{{ test.data.value.max_attempts || '∞' }}</strong></div>
          <label class="inline"><input type="checkbox" :checked="test.data.value.shuffle_questions" disabled /> перемешать</label>
          <label class="inline"><input type="checkbox" :checked="test.data.value.show_answers_after_submit" disabled /> показать разбор</label>
          <button class="btn btn--ghost btn--sm" @click="open('settings')">Изменить</button>
        </aside>
      </div>

      <section v-else-if="tab === 'settings'" class="card">
        <form class="form" @submit.prevent="saveSettings">
          <label>Название <input v-model="form.title" required /></label>
          <label>Описание <textarea v-model="form.description" /></label>
          <div class="form-row">
            <label>
              Режим
              <select v-model="form.mode">
                <option v-for="(label, key) in testModeLabels" :key="key" :value="key">{{ label }}</option>
              </select>
            </label>
            <label>Минут (0 — без таймера) <input v-model.number="form.time_limit_minutes" type="number" min="0" /></label>
            <label>Попыток (0 — без лимита) <input v-model.number="form.max_attempts" type="number" min="0" /></label>
            <label>Проходной % <input v-model.number="form.passing_score_pct" type="number" min="0" max="100" /></label>
          </div>
          <div class="form-row">
            <label>Доступен с <input v-model="form.available_from" type="datetime-local" /></label>
            <label>Доступен до <input v-model="form.available_to" type="datetime-local" /></label>
          </div>
          <label class="inline"><input v-model="form.shuffle_questions" type="checkbox" /> Перемешивать вопросы</label>
          <label class="inline"><input v-model="form.shuffle_options" type="checkbox" /> Перемешивать варианты</label>
          <label class="inline"><input v-model="form.show_answers_after_submit" type="checkbox" /> Показывать разбор после сдачи</label>
          <div class="row">
            <button class="btn" :disabled="busy">Сохранить</button>
            <button type="button" class="btn btn--danger" :disabled="busy" @click="removeTest">Удалить тест</button>
          </div>
        </form>
      </section>

      <section v-else-if="tab === 'stats'" class="stack">
        <StateBlock :loading="stats.loading.value" :error="stats.error.value" @retry="stats.run">
          <template v-if="stats.data.value">
            <div class="grid">
              <div class="card"><div class="stat">{{ stats.data.value.attempts }}</div><span class="muted">попыток</span></div>
              <div class="card"><div class="stat">{{ stats.data.value.students }}</div><span class="muted">учеников</span></div>
              <div class="card"><div class="stat">{{ stats.data.value.average_score_pct }}%</div><span class="muted">средний балл</span></div>
              <div class="card"><div class="stat">{{ stats.data.value.pass_rate_pct }}%</div><span class="muted">сдали</span></div>
              <div class="card"><div class="stat">{{ stats.data.value.anti_cheat_events }}</div><span class="muted">событий античита</span></div>
            </div>
            <div class="card table-wrap">
              <table class="table">
                <thead><tr><th>Вопрос</th><th>Тип</th><th>Ответили</th><th>Верно</th></tr></thead>
                <tbody>
                  <tr v-for="q in stats.data.value.questions" :key="q.question_id">
                    <td><MathText :text="q.text" /></td>
                    <td>{{ questionTypeLabels[q.type] }}</td>
                    <td>{{ q.answered }}</td>
                    <td :class="{ error: (q.correct_pct ?? 100) < 50 }">{{ q.correct_pct === null ? '—' : `${q.correct_pct}%` }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>
        </StateBlock>
      </section>

      <section v-else class="card">
        <StateBlock :loading="attempts.loading.value" :error="attempts.error.value" :empty="!attempts.data.value?.length" @retry="attempts.run">
          <div class="table-wrap">
            <table class="table">
              <thead><tr><th>Ученик</th><th>Начата</th><th>Статус</th><th>Балл</th><th></th></tr></thead>
              <tbody>
                <tr v-for="a in attempts.data.value ?? []" :key="a.id">
                  <td>{{ a.student_email }}</td>
                  <td>{{ fmtDateTime(a.started_at) }}</td>
                  <td><AppBadge :kind="a.status === 'submitted' ? 'warning' : a.is_passed ? 'success' : 'default'">{{ attemptStatusLabels[a.status] }}</AppBadge></td>
                  <td>{{ a.score }} / {{ a.max_score }} ({{ a.score_pct }}%)</td>
                  <td><RouterLink :to="`/attempts/${a.id}`" class="btn btn--ghost btn--sm">{{ a.status === 'submitted' ? 'Проверить' : 'Разбор' }}</RouterLink></td>
                </tr>
              </tbody>
            </table>
          </div>
        </StateBlock>
      </section>
    </template>
  </StateBlock>

  <AppModal v-if="picking" title="Добавить вопросы из банка" wide @close="picking = false">
    <form class="row" style="margin-bottom: 12px" @submit.prevent="bank.run">
      <input v-model="bankSearch" type="search" placeholder="Поиск" style="max-width: 280px" />
      <button class="btn btn--ghost">Найти</button>
      <RouterLink to="/teach/questions" class="small">Создать вопрос в банке →</RouterLink>
    </form>
    <StateBlock :loading="bank.loading.value" :error="bank.error.value" :empty="!bank.data.value?.results.length" @retry="bank.run">
      <ul class="list-plain">
        <li v-for="q in bank.data.value?.results ?? []" :key="q.id" class="row row--between">
          <span style="flex: 1"><AppBadge>{{ questionTypeLabels[q.type] }}</AppBadge> <MathText :text="q.text" /></span>
          <button class="btn btn--sm" :disabled="busy || inTest(q.id)" @click="add(q.id)">{{ inTest(q.id) ? 'В тесте' : 'Добавить' }}</button>
        </li>
      </ul>
    </StateBlock>
  </AppModal>
</template>

<style scoped>
.tq {
  display: grid;
  grid-template-columns: 16px minmax(0, 1fr) 72px auto auto;
  gap: var(--space-sm);
  align-items: center;
}
.tq__points {
  height: 36px;
  text-align: center;
  padding: 0 6px;
}
.add-q {
  display: block;
  width: 100%;
  margin-top: var(--space-sm);
  cursor: pointer;
  font: inherit;
}
.summary {
  display: grid;
  gap: var(--space-sm);
  font-size: var(--fs-body-sm);
}
</style>
