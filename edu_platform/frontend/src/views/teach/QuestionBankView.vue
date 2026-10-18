<script setup lang="ts">
import { reactive, ref } from 'vue'

import { questionsApi } from '@/api/tests'
import QuestionEditor from '@/components/teach/QuestionEditor.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
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
const filters = reactive({ topic: '' as number | '', type: '', search: '', page: 1 })
const questions = useAsync(() => questionsApi.list({
  topic: filters.topic || undefined, type: filters.type || undefined, search: filters.search || undefined,
  is_archived: false, page: filters.page,
}))
const topicForm = reactive({ subject: '', name: '' })
const editing = ref<Question | 'new' | null>(null)

function apply() {
  filters.page = 1
  questions.run()
}

async function addTopic() {
  if (await act(() => questionsApi.createTopic(topicForm), 'Тема создана')) {
    topicForm.name = ''
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
  <PageHeader title="Банк вопросов" subtitle="Общий для всей школы. Вопросы добавляются в тесты в редакторе теста.">
    <button class="btn" :disabled="!topics.data.value?.length" @click="editing = 'new'">+ Вопрос</button>
  </PageHeader>

  <div class="grid--2" style="grid-template-columns: minmax(240px, 1fr) 3fr; align-items: start">
    <section class="card">
      <h2>Темы</h2>
      <StateBlock :loading="topics.loading.value" :error="topics.error.value" :empty="!topics.data.value?.length"
                  empty-text="Создайте первую тему." @retry="topics.run">
        <ul class="list-plain">
          <li :class="{ selected: filters.topic === '' }" style="cursor: pointer" @click="filters.topic = ''; apply()">Все темы</li>
          <li v-for="t in topics.data.value ?? []" :key="t.id" :class="{ selected: filters.topic === t.id }"
              style="cursor: pointer" @click="filters.topic = t.id; apply()">
            {{ t.name }} <span class="muted small">{{ t.subject }} · {{ t.questions_count }}</span>
          </li>
        </ul>
      </StateBlock>
      <form class="form" style="margin-top: 12px" @submit.prevent="addTopic">
        <input v-model="topicForm.subject" placeholder="Предмет" required />
        <input v-model="topicForm.name" placeholder="Тема" required />
        <button class="btn btn--ghost" :disabled="busy">+ Тема</button>
      </form>
    </section>

    <section class="stack">
      <form class="row" @submit.prevent="apply">
        <input v-model="filters.search" type="search" placeholder="Поиск по тексту" style="max-width: 280px" />
        <select v-model="filters.type" style="max-width: 220px" @change="apply">
          <option value="">Все типы</option>
          <option v-for="(label, key) in questionTypeLabels" :key="key" :value="key">{{ label }}</option>
        </select>
        <button class="btn btn--ghost">Найти</button>
      </form>
      <StateBlock :loading="questions.loading.value" :error="questions.error.value"
                  :empty="!questions.data.value?.results.length" @retry="questions.run">
        <ul class="list-plain">
          <li v-for="q in questions.data.value?.results ?? []" :key="q.id" class="stack" style="gap: 6px">
            <div class="row row--between">
              <span class="row">
                <AppBadge>{{ questionTypeLabels[q.type] }}</AppBadge>
                <span class="muted small">сложность {{ q.difficulty }} · v{{ q.version }} · в тестах: {{ q.used_in_tests }}</span>
              </span>
              <span class="row">
                <button class="btn btn--ghost btn--sm" @click="editing = q">Изменить</button>
                <button class="btn btn--ghost btn--sm" @click="remove(q)">Удалить</button>
              </span>
            </div>
            <MathText :text="q.text" block />
            <span v-if="q.options.length" class="small muted">
              <span v-for="o in q.options" :key="o.id" :style="{ fontWeight: o.is_correct ? 700 : 400 }">
                <MathText :text="o.text" /><template v-if="o.match_target"> → {{ o.match_target }}</template>;
              </span>
            </span>
          </li>
        </ul>
        <AppPager :page="filters.page" :total-pages="questions.data.value?.total_pages ?? 1"
                  @change="(p) => { filters.page = p; questions.run() }" />
      </StateBlock>
    </section>
  </div>

  <AppModal v-if="editing" :title="editing === 'new' ? 'Новый вопрос' : 'Изменить вопрос'" wide @close="editing = null">
    <QuestionEditor :question="editing === 'new' ? undefined : editing" :topics="topics.data.value ?? []" :busy="busy" @save="save" />
  </AppModal>
</template>

<style scoped>
.selected {
  border-color: var(--primary) !important;
}
</style>
