<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

import { questionsApi, testsApi } from '@/api/tests'
import QuestionEditor from '@/components/teach/QuestionEditor.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppPager from '@/components/ui/AppPager.vue'
import MathText from '@/components/ui/MathText.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAction, useAsync } from '@/composables/useAsync'
import type { Question } from '@/types/api'
import { questionTypeLabels } from '@/utils/format'

const { act, busy } = useAction()
const topics = useAsync(() => questionsApi.topics())
const filters = reactive({ topic: '' as number | '', type: '', difficulty: '' as number | '', search: '', page: 1 })
const questions = useAsync(() => questionsApi.list({
  topic: filters.topic || undefined, type: filters.type || undefined, difficulty: filters.difficulty || undefined,
  search: filters.search || undefined, is_archived: false, page: filters.page,
}))
const topicForm = reactive({ subject: '', name: '' })
const addingTopic = ref(false)
const editing = ref<Question | 'new' | null>(null)
const selected = ref<Set<number>>(new Set())
const tests = useAsync(() => testsApi.list(), { immediate: false })
const targetTest = ref<number | ''>('')
const totalAll = computed(() => (topics.data.value ?? []).reduce((n, t) => n + t.questions_count, 0))

function apply() {
  filters.page = 1
  questions.run()
}

function pickTopic(id: number | '') {
  filters.topic = id
  apply()
}

function toggle(id: number) {
  const next = new Set(selected.value)
  if (next.has(id)) next.delete(id)
  else next.add(id)
  selected.value = next
  if (next.size && !tests.data.value) tests.run()
}

async function addSelectedToTest() {
  if (!targetTest.value) return
  const testId = Number(targetTest.value)
  const ids = [...selected.value]
  const ok = await act(async () => {
    for (const id of ids) await testsApi.addQuestion(testId, id, 1)
    return true
  }, `Добавлено в тест: ${ids.length}`)
  if (ok) selected.value = new Set()
}

async function addTopic() {
  if (await act(() => questionsApi.createTopic(topicForm), 'Тема создана')) {
    topicForm.name = ''
    addingTopic.value = false
    topics.run()
  }
}

async function save(payload: Partial<Question>) {
  const current = editing.value
  const ok = await act(() => (current && current !== 'new' ? questionsApi.update(current.id, payload) : questionsApi.create(payload)), 'Вопрос сохранён')
  if (ok) {
    editing.value = null
    questions.run()
    topics.run()
  }
}

async function remove(q: Question) {
  if (!confirm('Удалить вопрос? Если он уже в тестах — будет перенесён в архив.')) return
  if (await act(() => questionsApi.remove(q.id), 'Готово')) questions.run()
}
</script>

<template>
  <PageHeader title="Банк вопросов" subtitle="Общий для всей школы — вопросы добавляются в тесты." />

  <div class="card card--flush bank">
    <aside class="topics">
      <strong>Темы</strong>
      <StateBlock :loading="topics.loading.value" :error="topics.error.value" @retry="topics.run">
        <nav class="side-nav">
          <button :class="{ active: filters.topic === '' }" @click="pickTopic('')"><span>Все</span><span>{{ totalAll }}</span></button>
          <button v-for="t in topics.data.value ?? []" :key="t.id" :class="{ active: filters.topic === t.id }" @click="pickTopic(t.id)">
            <span>{{ t.name }}</span><span>{{ t.questions_count }}</span>
          </button>
        </nav>
      </StateBlock>
      <form v-if="addingTopic" class="form" @submit.prevent="addTopic">
        <input v-model="topicForm.subject" placeholder="Предмет" required />
        <input v-model="topicForm.name" placeholder="Тема" required />
        <button class="btn btn--sm" :disabled="busy">Создать</button>
      </form>
      <button v-else class="dropzone add-topic" @click="addingTopic = true">+ тема</button>
    </aside>

    <section class="questions">
      <form class="row" @submit.prevent="apply">
        <div class="search" style="flex: 1; min-width: 200px">
          <AppIcon name="search" /><input v-model="filters.search" type="search" placeholder="Поиск…" aria-label="Поиск вопросов" />
        </div>
        <select v-model="filters.type" style="width: auto" aria-label="Тип" @change="apply">
          <option value="">Тип</option>
          <option v-for="(label, key) in questionTypeLabels" :key="key" :value="key">{{ label }}</option>
        </select>
        <select v-model="filters.difficulty" style="width: auto" aria-label="Сложность" @change="apply">
          <option value="">Сложн.</option>
          <option v-for="d in 5" :key="d" :value="d">{{ d }}</option>
        </select>
        <button type="button" class="btn" :disabled="!topics.data.value?.length" @click="editing = 'new'">+ Вопрос</button>
      </form>

      <StateBlock :loading="questions.loading.value" :error="questions.error.value"
                  :empty="!questions.data.value?.results.length" @retry="questions.run">
        <div class="table-wrap">
          <table class="table">
            <thead><tr><th style="width: 32px"></th><th>Вопрос</th><th>Тип</th><th>Сл.</th><th>В тестах</th><th></th></tr></thead>
            <tbody>
              <tr v-for="q in questions.data.value?.results ?? []" :key="q.id">
                <td><input type="checkbox" :checked="selected.has(q.id)" :aria-label="`Выбрать вопрос ${q.id}`" @change="toggle(q.id)" /></td>
                <td class="q-text"><MathText :text="q.text" /></td>
                <td class="small">{{ questionTypeLabels[q.type] }}</td>
                <td>{{ q.difficulty }}</td>
                <td>{{ q.used_in_tests }}</td>
                <td class="row" style="flex-wrap: nowrap">
                  <button class="btn btn--text btn--sm" @click="editing = q"><AppIcon name="edit" :size="14" /></button>
                  <button class="btn btn--text btn--sm" @click="remove(q)"><AppIcon name="trash" :size="14" /></button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <AppPager :page="filters.page" :total-pages="questions.data.value?.total_pages ?? 1" @change="(p) => { filters.page = p; questions.run() }" />
      </StateBlock>

      <div v-if="selected.size" class="selection">
        <span>Выбрано {{ selected.size }} · Добавить в тест</span>
        <select v-model="targetTest" aria-label="Тест">
          <option value="">— выберите тест —</option>
          <option v-for="t in tests.data.value?.results ?? []" :key="t.id" :value="t.id">{{ t.title }}</option>
        </select>
        <button class="btn btn--sm" :disabled="busy || !targetTest" @click="addSelectedToTest">Добавить</button>
        <button class="btn btn--text btn--sm" @click="selected = new Set()">Сбросить</button>
      </div>
    </section>
  </div>

  <AppModal v-if="editing" :title="editing === 'new' ? 'Новый вопрос' : 'Изменить вопрос'" wide @close="editing = null">
    <QuestionEditor :question="editing === 'new' ? undefined : editing" :topics="topics.data.value ?? []" :busy="busy" @save="save" />
  </AppModal>
</template>

<style scoped>
.bank {
  display: grid;
  grid-template-columns: 240px minmax(0, 1fr);
  min-height: 480px;
}
.topics {
  padding: var(--space-lg);
  border-right: 1px solid var(--border-default);
  background: var(--surface-subtle);
  display: grid;
  gap: var(--space-sm);
  align-content: start;
}
.add-topic {
  cursor: pointer;
  font: inherit;
}
.questions {
  padding: var(--space-lg);
  display: grid;
  gap: var(--space-md);
  align-content: start;
  min-width: 0;
}
.q-text {
  max-width: 420px;
}
.selection {
  position: sticky;
  bottom: var(--space-md);
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
  padding: var(--space-sm) var(--space-md);
  border-radius: var(--radius-md);
  background: var(--teal-900);
  color: var(--text-on-dark);
  box-shadow: var(--shadow-3);
}
.selection select {
  width: auto;
  min-width: 220px;
  height: 36px;
}
.selection .btn--text {
  color: var(--text-on-dark-muted);
}
@media (max-width: 860px) {
  .bank {
    grid-template-columns: 1fr;
  }
  .topics {
    border-right: 0;
    border-bottom: 1px solid var(--border-default);
  }
}
</style>
