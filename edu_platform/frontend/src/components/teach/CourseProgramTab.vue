<script setup lang="ts">
import { computed, reactive, ref, watch } from 'vue'

import { lessonsApi, sectionsApi } from '@/api/content'
import AppIcon from '@/components/ui/AppIcon.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAction, useAsync } from '@/composables/useAsync'
import type { Lesson, Section } from '@/types/api'

/** Конструктор курса (вайрфрейм 1l): дерево разделов/уроков + редактор выбранного урока */
const props = defineProps<{ courseId: number }>()
const emit = defineEmits<{ tab: [name: string] }>()
const { act, busy } = useAction()

const sections = useAsync(() => sectionsApi.list(props.courseId))
const lessons = useAsync(() => lessonsApi.list({ course: props.courseId }))
const selectedId = ref<number | null>(null)
const adding = ref<'section' | number | null>(null)
const newTitle = ref('')
const form = reactive({ title: '', is_free_preview: false })

const lessonsOf = (sectionId: number) => (lessons.data.value ?? []).filter((l) => l.section === sectionId)
const selected = computed<Lesson | null>(() => (lessons.data.value ?? []).find((l) => l.id === selectedId.value) ?? null)

watch(selected, (l) => Object.assign(form, { title: l?.title ?? '', is_free_preview: l?.is_free_preview ?? false }))
watch(() => lessons.data.value, (list) => {
  if (list?.length && selectedId.value === null) selectedId.value = list[0].id
})

async function addSection() {
  const order = (sections.data.value?.length ?? 0) + 1
  if (await act(() => sectionsApi.create({ course: props.courseId, title: newTitle.value, order }))) {
    newTitle.value = ''
    adding.value = null
    sections.run()
  }
}

async function addLesson(sectionId: number) {
  const order = lessonsOf(sectionId).length + 1
  const lesson = await act(() => lessonsApi.create({ section: sectionId, title: newTitle.value, order }))
  if (lesson) {
    newTitle.value = ''
    adding.value = null
    await lessons.run()
    selectedId.value = lesson.id
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

async function saveLesson(publishNow = false) {
  if (!selected.value) return
  const payload: Partial<Lesson> = { ...form }
  if (publishNow) payload.publish_at = null
  if (await act(() => lessonsApi.update(selected.value!.id, payload), publishNow ? 'Урок опубликован' : 'Урок сохранён')) lessons.run()
}
</script>

<template>
  <StateBlock :loading="sections.loading.value" :error="sections.error.value" @retry="sections.run">
    <div class="card card--flush builder">
      <aside class="tree">
        <strong>Программа</strong>
        <div v-for="s in sections.data.value ?? []" :key="s.id" class="tree__section">
          <div class="tree__section-head">
            <span class="row"><AppIcon name="chevron-down" :size="14" /> {{ s.title }}</span>
            <span class="tree__tools">
              <button class="btn btn--text btn--sm" title="Переименовать" @click="renameSection(s)"><AppIcon name="edit" :size="13" /></button>
              <button class="btn btn--text btn--sm" title="Удалить" @click="removeSection(s)"><AppIcon name="trash" :size="13" /></button>
            </span>
          </div>
          <nav class="side-nav">
            <button v-for="l in lessonsOf(s.id)" :key="l.id" :class="{ active: selectedId === l.id }" @click="selectedId = l.id">
              <span>{{ l.title }}</span>
              <span v-if="!l.is_published" class="draft">черновик</span>
              <span v-else class="live" title="Опубликован" />
            </button>
          </nav>
          <form v-if="adding === s.id" class="row" @submit.prevent="addLesson(s.id)">
            <input v-model="newTitle" placeholder="Название урока" required autofocus style="height: 36px" />
            <button class="btn btn--sm" :disabled="busy">OK</button>
          </form>
          <button v-else class="btn btn--text btn--sm add" @click="adding = s.id; newTitle = ''">+ урок</button>
        </div>
        <form v-if="adding === 'section'" class="row" @submit.prevent="addSection">
          <input v-model="newTitle" placeholder="Название раздела" required autofocus style="height: 36px" />
          <button class="btn btn--sm" :disabled="busy">OK</button>
        </form>
        <button v-else class="dropzone add-section" @click="adding = 'section'; newTitle = ''">+ раздел</button>
      </aside>

      <section class="editor">
        <template v-if="selected">
          <input v-model="form.title" class="editor__title" aria-label="Название урока" />
          <div class="editor__adds">
            <RouterLink :to="`/teach/lessons/${selected.id}`" class="dropzone add-tile"><AppIcon name="play" :size="16" /> + YouTube</RouterLink>
            <RouterLink :to="`/teach/lessons/${selected.id}`" class="dropzone add-tile"><AppIcon name="file" :size="16" /> + файл</RouterLink>
            <button class="dropzone add-tile" @click="emit('tab', 'tests')"><AppIcon name="check" :size="16" /> + тест</button>
          </div>
          <div class="row row--between">
            <label class="inline"><input v-model="form.is_free_preview" type="checkbox" /> бесплатное превью</label>
            <div class="row">
              <RouterLink :to="`/lessons/${selected.id}`" class="btn btn--text btn--sm">Как видит ученик</RouterLink>
              <button class="btn btn--ghost btn--sm" :disabled="busy" @click="saveLesson()">Сохранить</button>
              <button v-if="!selected.is_published" class="btn btn--sm" :disabled="busy" @click="saveLesson(true)">Опубликовать</button>
            </div>
          </div>
          <p class="muted small">
            Видео, материалы, дату публикации и порядок — в <RouterLink :to="`/teach/lessons/${selected.id}`">полном редакторе урока</RouterLink>.
          </p>
        </template>
        <p v-else class="muted">Добавьте раздел и урок слева, чтобы начать.</p>
      </section>
    </div>
  </StateBlock>
</template>

<style scoped>
.builder {
  display: grid;
  grid-template-columns: 300px minmax(0, 1fr);
  min-height: 380px;
}
.tree {
  padding: var(--space-lg);
  border-right: 1px solid var(--border-default);
  background: var(--surface-subtle);
  display: grid;
  gap: var(--space-md);
  align-content: start;
}
.tree__section {
  display: grid;
  gap: 4px;
}
.tree__section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font: 600 var(--fs-body-sm) / 1.3 var(--font-sans);
}
.tree__tools {
  display: flex;
  opacity: 0.6;
}
.tree .side-nav {
  padding-left: var(--space-md);
}
.draft {
  font-size: var(--fs-micro);
  color: var(--warning-text);
}
.live {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--green-dark);
  align-self: center;
}
.add {
  justify-self: start;
  margin-left: var(--space-md);
}
.add-section {
  cursor: pointer;
  font: inherit;
}
.editor {
  padding: var(--space-xl);
  display: grid;
  gap: var(--space-lg);
  align-content: start;
}
.editor__title {
  font: 500 var(--fs-h4) / 1.3 var(--font-sans);
  height: var(--control-height-lg);
}
.editor__adds {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-sm);
}
.add-tile {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: var(--space-xs);
  min-height: 64px;
  color: var(--text-strong);
  cursor: pointer;
  font: 500 var(--fs-body-sm) / 1 var(--font-sans);
  text-decoration: none;
}
.add-tile:hover {
  border-color: var(--green-dark);
  background: var(--surface-feature);
  text-decoration: none;
}
@media (max-width: 860px) {
  .builder {
    grid-template-columns: 1fr;
  }
  .tree {
    border-right: 0;
    border-bottom: 1px solid var(--border-default);
  }
}
</style>
