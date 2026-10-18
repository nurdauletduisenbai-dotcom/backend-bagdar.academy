<script setup lang="ts">
import { reactive } from 'vue'
import { useRouter } from 'vue-router'

import { testsApi } from '@/api/tests'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAction, useAsync } from '@/composables/useAsync'
import type { TestMode } from '@/types/api'
import { testModeLabels } from '@/utils/format'

const props = defineProps<{ courseId: number }>()
const router = useRouter()
const { act, busy } = useAction()
const tests = useAsync(() => testsApi.list({ course: props.courseId }))
const form = reactive({ title: '', mode: 'quiz' as TestMode, time_limit_minutes: 20, max_attempts: 2, passing_score_pct: 60 })

async function create() {
  const test = await act(() => testsApi.create({ ...form, course: props.courseId }), 'Тест создан')
  if (test) router.push(`/teach/tests/${test.id}`)
}
</script>

<template>
  <div class="grid--2" style="align-items: start">
    <section class="card">
      <h2>Тесты курса</h2>
      <StateBlock :loading="tests.loading.value" :error="tests.error.value" :empty="!tests.data.value?.results.length" @retry="tests.run">
        <ul class="list-plain">
          <li v-for="t in tests.data.value?.results ?? []" :key="t.id" class="row row--between">
            <RouterLink :to="`/teach/tests/${t.id}`">{{ t.title }}</RouterLink>
            <span class="muted small">{{ testModeLabels[t.mode] }} · {{ t.questions_count }} вопр.</span>
          </li>
        </ul>
      </StateBlock>
    </section>
    <section class="card">
      <h2>Новый тест</h2>
      <form class="form" @submit.prevent="create">
        <label>Название <input v-model="form.title" required /></label>
        <div class="form-row">
          <label>
            Режим
            <select v-model="form.mode">
              <option v-for="(label, key) in testModeLabels" :key="key" :value="key">{{ label }}</option>
            </select>
          </label>
          <label>Минут (0 — без таймера) <input v-model.number="form.time_limit_minutes" type="number" min="0" /></label>
        </div>
        <div class="form-row">
          <label>Попыток (0 — без лимита) <input v-model.number="form.max_attempts" type="number" min="0" /></label>
          <label>Проходной % <input v-model.number="form.passing_score_pct" type="number" min="0" max="100" /></label>
        </div>
        <button class="btn" :disabled="busy" style="justify-self: start">Создать и добавить вопросы</button>
      </form>
    </section>
  </div>
</template>
