<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { lessonsApi, materialsApi, videosApi } from '@/api/content'
import PageHeader from '@/components/ui/PageHeader.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAction, useAsync } from '@/composables/useAsync'
import { fmtBytes, fmtDuration, fromLocalInput, toLocalInput } from '@/utils/format'

const props = defineProps<{ id: string }>()
const lessonId = Number(props.id)
const router = useRouter()
const { act, busy } = useAction()

const form = reactive({ title: '', order: 1, is_free_preview: false, publish_at: '' })
const lesson = useAsync(async () => {
  const l = await lessonsApi.get(lessonId)
  Object.assign(form, { title: l.title, order: l.order, is_free_preview: l.is_free_preview, publish_at: toLocalInput(l.publish_at) })
  return l
})
const videos = useAsync(() => videosApi.list(lessonId))
const materials = useAsync(() => materialsApi.list(lessonId))

const video = reactive({ title: '', youtube_url: '', minutes: 10 })
const material = reactive({ title: '', file_url: '' })
const file = ref<File | null>(null)
const fileInput = ref<HTMLInputElement | null>(null)

async function saveLesson() {
  if (await act(() => lessonsApi.update(lessonId, { ...form, publish_at: fromLocalInput(form.publish_at) }), 'Урок сохранён')) lesson.run()
}

async function removeLesson() {
  if (!confirm('Удалить урок?')) return
  const courseId = lesson.data.value?.course_id
  if (await act(() => lessonsApi.remove(lessonId), 'Урок удалён')) router.push(`/teach/courses/${courseId}`)
}

async function addVideo() {
  const ok = await act(() => videosApi.create({
    lesson: lessonId, title: video.title, youtube_url: video.youtube_url, duration_seconds: Math.round(video.minutes * 60),
  }), 'Видео добавлено')
  if (ok) {
    Object.assign(video, { title: '', youtube_url: '' })
    videos.run()
  }
}

async function removeVideo(id: number) {
  if (await act(() => videosApi.remove(id), 'Видео удалено')) videos.run()
}

async function addMaterial() {
  const ok = await act(() => materialsApi.create({ lesson: lessonId, title: material.title, file: file.value, file_url: material.file_url }),
    'Материал добавлен')
  if (ok) {
    Object.assign(material, { title: '', file_url: '' })
    file.value = null
    if (fileInput.value) fileInput.value.value = ''
    materials.run()
  }
}

async function removeMaterial(id: number) {
  if (await act(() => materialsApi.remove(id), 'Материал удалён')) materials.run()
}
</script>

<template>
  <StateBlock :loading="lesson.loading.value && !lesson.data.value" :error="lesson.error.value" @retry="lesson.run">
    <template v-if="lesson.data.value">
      <PageHeader :title="`Урок: ${lesson.data.value.title}`">
        <template #before><RouterLink :to="`/teach/courses/${lesson.data.value.course_id}`" class="small">← Редактор курса</RouterLink></template>
        <RouterLink :to="`/lessons/${id}`" class="btn btn--ghost">Как видит ученик</RouterLink>
      </PageHeader>

      <div class="grid--2" style="align-items: start">
        <section class="card">
          <h2>Параметры</h2>
          <form class="form" @submit.prevent="saveLesson">
            <label>Название <input v-model="form.title" required /></label>
            <div class="form-row">
              <label>Порядок <input v-model.number="form.order" type="number" min="1" /></label>
              <label>Публикация (пусто — сразу) <input v-model="form.publish_at" type="datetime-local" /></label>
            </div>
            <label class="inline"><input v-model="form.is_free_preview" type="checkbox" /> Бесплатный превью-урок</label>
            <div class="row">
              <button class="btn" :disabled="busy">Сохранить</button>
              <button type="button" class="btn btn--danger" :disabled="busy" @click="removeLesson">Удалить урок</button>
            </div>
          </form>
        </section>

        <section class="card">
          <h2>Видео (YouTube)</h2>
          <StateBlock :loading="videos.loading.value" :error="videos.error.value" :empty="!videos.data.value?.length" @retry="videos.run">
            <ul class="list-plain">
              <li v-for="v in videos.data.value ?? []" :key="v.id" class="row row--between">
                <span>{{ v.title }} <span class="muted small">{{ v.youtube_video_id }} · {{ fmtDuration(v.duration_seconds) }}</span></span>
                <button class="btn btn--ghost btn--sm" @click="removeVideo(v.id)">Удалить</button>
              </li>
            </ul>
          </StateBlock>
          <form class="form" style="margin-top: 12px" @submit.prevent="addVideo">
            <label>Название <input v-model="video.title" required /></label>
            <label>Ссылка YouTube (лучше «доступ по ссылке») <input v-model="video.youtube_url" placeholder="https://youtu.be/…" required /></label>
            <label>Длительность, мин <input v-model.number="video.minutes" type="number" min="0" step="0.5" /></label>
            <button class="btn btn--ghost" :disabled="busy" style="justify-self: start">+ Видео</button>
          </form>
        </section>

        <section class="card" style="grid-column: 1 / -1">
          <h2>Материалы</h2>
          <StateBlock :loading="materials.loading.value" :error="materials.error.value" :empty="!materials.data.value?.length" @retry="materials.run">
            <ul class="list-plain">
              <li v-for="m in materials.data.value ?? []" :key="m.id" class="row row--between">
                <span>{{ m.title }} <span class="muted small">{{ m.has_file ? `${m.file_type} ${fmtBytes(m.file_size_bytes)}` : m.file_url }}</span></span>
                <button class="btn btn--ghost btn--sm" @click="removeMaterial(m.id)">Удалить</button>
              </li>
            </ul>
          </StateBlock>
          <form class="form-row" style="margin-top: 12px; align-items: end" @submit.prevent="addMaterial">
            <label>Название <input v-model="material.title" required /></label>
            <label>Файл (pdf, docx, pptx, zip…, до 20 МБ)
              <input ref="fileInput" type="file" @change="file = ($event.target as HTMLInputElement).files?.[0] ?? null" />
            </label>
            <label>…или ссылка <input v-model="material.file_url" type="url" /></label>
            <button class="btn btn--ghost" :disabled="busy">+ Материал</button>
          </form>
        </section>
      </div>
    </template>
  </StateBlock>
</template>
