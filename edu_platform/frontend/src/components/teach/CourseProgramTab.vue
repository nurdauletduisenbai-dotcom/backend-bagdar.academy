<script setup lang="ts">
import { ref } from 'vue'

import { lessonsApi, sectionsApi } from '@/api/content'
import AppBadge from '@/components/ui/AppBadge.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAction, useAsync } from '@/composables/useAsync'
import type { Section } from '@/types/api'

const props = defineProps<{ courseId: number }>()
const { act, busy } = useAction()

const sections = useAsync(() => sectionsApi.list(props.courseId))
const lessons = useAsync(() => lessonsApi.list({ course: props.courseId }))
const newSection = ref('')
const newLesson = ref<Record<number, string>>({})

const lessonsOf = (sectionId: number) => (lessons.data.value ?? []).filter((l) => l.section === sectionId)

async function addSection() {
  const order = (sections.data.value?.length ?? 0) + 1
  if (await act(() => sectionsApi.create({ course: props.courseId, title: newSection.value, order }))) {
    newSection.value = ''
    sections.run()
  }
}

async function renameSection(s: Section) {
  const title = prompt('Название раздела', s.title)
  if (title && (await act(() => sectionsApi.update(s.id, { title })))) sections.run()
}

async function removeSection(s: Section) {
  if (!confirm(`Удалить раздел «${s.title}» вместе с уроками?`)) return
  if (await act(() => sectionsApi.remove(s.id), 'Раздел удалён')) {
    sections.run()
    lessons.run()
  }
}

async function addLesson(sectionId: number) {
  const title = newLesson.value[sectionId]
  if (!title) return
  const order = lessonsOf(sectionId).length + 1
  if (await act(() => lessonsApi.create({ section: sectionId, title, order }))) {
    newLesson.value[sectionId] = ''
    lessons.run()
  }
}
</script>

<template>
  <StateBlock :loading="sections.loading.value" :error="sections.error.value" @retry="sections.run">
    <div class="stack">
      <section v-for="s in sections.data.value ?? []" :key="s.id" class="card">
        <div class="row row--between">
          <h2>{{ s.order }}. {{ s.title }}</h2>
          <span class="row">
            <button class="btn btn--ghost btn--sm" @click="renameSection(s)">Переименовать</button>
            <button class="btn btn--ghost btn--sm" @click="removeSection(s)">Удалить</button>
          </span>
        </div>
        <ul class="list-plain">
          <li v-for="l in lessonsOf(s.id)" :key="l.id" class="row row--between">
            <RouterLink :to="`/teach/lessons/${l.id}`">{{ l.order }}. {{ l.title }}</RouterLink>
            <span class="row">
              <AppBadge v-if="l.is_free_preview" kind="info">Превью</AppBadge>
              <AppBadge v-if="!l.is_published" kind="warning">Отложен</AppBadge>
              <RouterLink :to="`/lessons/${l.id}`" class="btn btn--ghost btn--sm">Как видит ученик</RouterLink>
            </span>
          </li>
        </ul>
        <form class="row" style="margin-top: 10px" @submit.prevent="addLesson(s.id)">
          <input v-model="newLesson[s.id]" placeholder="Название нового урока" style="max-width: 360px" />
          <button class="btn btn--ghost btn--sm" :disabled="busy">+ Урок</button>
        </form>
      </section>

      <form class="card row" @submit.prevent="addSection">
        <input v-model="newSection" placeholder="Название нового раздела" style="max-width: 360px" required />
        <button class="btn" :disabled="busy">+ Раздел</button>
      </form>
    </div>
  </StateBlock>
</template>
