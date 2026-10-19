<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'

import { lessonsApi, videosApi } from '@/api/content'
import { downloadFile, errorMessage } from '@/api/http'
import LessonComments from '@/components/course/LessonComments.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAction, useAsync } from '@/composables/useAsync'
import { useYouTubeProgress, withJsApi } from '@/composables/useYouTubeProgress'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/stores/toast'
import type { Material, VideoPlayer } from '@/types/api'
import { fmtBytes, fmtDateTime, fmtDuration, testModeLabels } from '@/utils/format'

const props = defineProps<{ id: string }>()
const auth = useAuthStore()
const toast = useToast()
const { act, busy } = useAction()

const lesson = useAsync(async () => {
  const data = await lessonsApi.get(Number(props.id))
  if (data.videos.length && !player.value) nextTick(() => play(data.videos[0].id))
  return data
})

const player = ref<VideoPlayer | null>(null)
const iframe = ref<HTMLIFrameElement | null>(null)
const playerError = ref('')
const tab = ref<'materials' | 'assignments' | 'tests' | 'discussion'>('materials')

const counts = computed(() => ({
  materials: lesson.data.value?.materials.length ?? 0,
  assignments: lesson.data.value?.assignments.length ?? 0,
  tests: lesson.data.value?.tests.length ?? 0,
}))

const progress = useYouTubeProgress((videoId, completed) => {
  const v = lesson.data.value?.videos.find((x) => x.id === videoId)
  if (v && completed && !v.is_completed) {
    v.is_completed = true
    toast.success('Видео просмотрено')
    lesson.run()
  }
})

async function play(videoId: number) {
  playerError.value = ''
  try {
    player.value = await videosApi.play(videoId)
    await nextTick()
    progress.attach(iframe, videoId)
  } catch (e) {
    player.value = null
    playerError.value = errorMessage(e)
  }
}

async function complete() {
  await act(() => lessonsApi.complete(Number(props.id)), 'Урок отмечен пройденным')
  lesson.run()
}

async function download(m: Material) {
  await act(() => downloadFile(m.download_url!, m.title))
}
</script>

<template>
  <StateBlock :loading="lesson.loading.value && !lesson.data.value" :error="lesson.error.value" @retry="lesson.run">
    <template v-if="lesson.data.value">
      <!-- Кинотеатр -->
      <section class="band page-band cinema">
        <RouterLink :to="`/courses/${lesson.data.value.course_id}`" class="back small muted">
          <AppIcon name="arrow-left" :size="14" /> К курсу
        </RouterLink>
        <div v-if="lesson.data.value.videos.length" class="cinema__grid">
          <div class="video">
            <iframe v-if="player" ref="iframe" :key="player.video_id" :src="withJsApi(player.embed_url)" :title="player.title"
                    allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen />
            <div v-else class="video__empty">
              <AppIcon name="play" :size="32" />
              <span>{{ playerError || 'Загружаем видео…' }}</span>
            </div>
          </div>
          <div class="parts">
            <div class="eyebrow">Видео урока</div>
            <button v-for="(v, i) in lesson.data.value.videos" :key="v.id" class="part"
                    :class="{ active: player?.video_id === v.id }" @click="play(v.id)">
              <AppIcon :name="v.is_completed ? 'check' : 'play'" :size="14" />
              <span class="part__title">Часть {{ i + 1 }} · {{ v.title }}</span>
              <span class="part__time">{{ fmtDuration(v.duration_seconds) }}</span>
            </button>
            <span class="muted small">Видео засчитывается после просмотра 90%</span>
          </div>
        </div>
        <p v-else class="muted">В этом уроке нет видео — материалы и задания ниже.</p>
      </section>

      <div class="title-row">
        <h1>{{ lesson.data.value.title }}</h1>
        <div class="row">
          <RouterLink v-if="auth.isTeacher" :to="`/teach/lessons/${id}`" class="btn btn--ghost">Редактировать</RouterLink>
          <span v-if="lesson.data.value.is_completed" class="btn btn--ghost done"><AppIcon name="check" :size="16" /> Пройден</span>
          <button v-else-if="lesson.data.value.has_access && auth.isStudent" class="btn" :disabled="busy" @click="complete">
            Отметить пройденным
          </button>
        </div>
      </div>

      <div v-if="!lesson.data.value.has_access" class="alert alert--warning" style="margin-bottom: var(--space-lg)">
        Это бесплатный урок. Материалы, задания и остальные уроки откроются после записи на курс.
        <RouterLink :to="`/courses/${lesson.data.value.course_id}`" class="btn btn--sm">Записаться</RouterLink>
      </div>

      <template v-else>
        <div class="tabs">
          <button :class="{ active: tab === 'materials' }" @click="tab = 'materials'">Материалы {{ counts.materials }}</button>
          <button :class="{ active: tab === 'assignments' }" @click="tab = 'assignments'">ДЗ {{ counts.assignments }}</button>
          <button :class="{ active: tab === 'tests' }" @click="tab = 'tests'">Тест {{ counts.tests }}</button>
          <button :class="{ active: tab === 'discussion' }" @click="tab = 'discussion'">Обсуждение</button>
        </div>

        <div v-if="tab === 'materials'" class="stack">
          <p v-if="!counts.materials" class="muted">Материалов нет.</p>
          <div v-for="m in lesson.data.value.materials" :key="m.id" class="card file-row">
            <AppIcon name="file" />
            <span class="file-row__name">{{ m.title }} <span class="muted small">{{ m.file_type }} {{ fmtBytes(m.file_size_bytes) }}</span></span>
            <button v-if="m.has_file" class="btn btn--text btn--sm" :disabled="busy" @click="download(m)"><AppIcon name="download" :size="16" /> Скачать</button>
            <a v-else :href="m.file_url" target="_blank" rel="noopener" class="btn btn--text btn--sm"><AppIcon name="link" :size="16" /> Открыть</a>
          </div>
        </div>

        <div v-else-if="tab === 'assignments'" class="stack">
          <p v-if="!counts.assignments" class="muted">Домашних заданий нет.</p>
          <RouterLink v-for="a in lesson.data.value.assignments" :key="a.id" :to="`/assignments/${a.id}`" class="card card--link file-row">
            <AppIcon name="edit" />
            <span class="file-row__name">{{ a.title }}</span>
            <span class="muted small">до {{ fmtDateTime(a.deadline) }}</span>
          </RouterLink>
        </div>

        <div v-else-if="tab === 'tests'" class="stack">
          <p v-if="!counts.tests" class="muted">Тестов нет.</p>
          <RouterLink v-for="t in lesson.data.value.tests" :key="t.id" :to="`/tests/${t.id}/take`" class="card card--link file-row">
            <AppIcon name="check" />
            <span class="file-row__name">{{ t.title }}</span>
            <span class="muted small">{{ testModeLabels[t.mode] }}</span>
          </RouterLink>
        </div>

        <LessonComments v-else :lesson-id="Number(id)" :can-moderate="auth.isStaff" />
      </template>
    </template>
  </StateBlock>
</template>

<style scoped>
.back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-bottom: var(--space-md);
}
.band .back {
  color: var(--text-on-dark-muted);
}
.cinema {
  padding-bottom: var(--space-xxl);
}
.cinema__grid {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  gap: var(--space-xl);
  align-items: start;
}
.video {
  position: relative;
  aspect-ratio: 16 / 9;
  background: #000;
  border-radius: var(--radius-md);
  overflow: hidden;
}
/* YouTube API подменяет iframe — у нового элемента нет scoped-атрибута, поэтому :deep */
.video :deep(iframe) {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border: 0;
}
.video__empty {
  position: absolute;
  inset: 0;
  display: grid;
  place-content: center;
  justify-items: center;
  gap: var(--space-xs);
  color: var(--text-on-dark-muted);
  border: 1px dashed rgba(255, 255, 255, 0.25);
  border-radius: var(--radius-md);
}
.parts {
  display: grid;
  gap: var(--space-xs);
}
.part {
  display: grid;
  grid-template-columns: 16px minmax(0, 1fr) auto;
  gap: var(--space-xs);
  align-items: center;
  padding: 10px 12px;
  border-radius: var(--radius-md);
  border: 1px solid transparent;
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-on-dark);
  font: 500 var(--fs-body-sm) / 1.3 var(--font-sans);
  text-align: left;
  cursor: pointer;
}
.part:hover {
  background: rgba(255, 255, 255, 0.1);
}
.part.active {
  border-color: var(--green-500);
  background: rgba(0, 237, 100, 0.08);
}
.part__time {
  color: var(--text-on-dark-muted);
  font-size: var(--fs-caption);
}
.title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-md);
  flex-wrap: wrap;
  margin-bottom: var(--space-lg);
}
.done {
  color: var(--green-dark);
  border-color: var(--green-500);
  cursor: default;
}
.file-row {
  display: grid;
  grid-template-columns: 20px minmax(0, 1fr) auto;
  gap: var(--space-sm);
  align-items: center;
  padding: var(--space-sm) var(--space-md);
  color: inherit;
}
.file-row__name {
  font-weight: 500;
}
@media (max-width: 960px) {
  .cinema__grid {
    grid-template-columns: 1fr;
  }
}
</style>
