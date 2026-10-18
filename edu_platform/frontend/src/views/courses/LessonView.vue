<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'

import { lessonsApi, videosApi } from '@/api/content'
import { downloadFile, errorMessage } from '@/api/http'
import LessonComments from '@/components/course/LessonComments.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
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
const canModerate = computed(() => auth.isStaff)

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
      <PageHeader :title="lesson.data.value.title">
        <template #before>
          <RouterLink :to="`/courses/${lesson.data.value.course_id}`" class="small">← К курсу</RouterLink>
        </template>
        <AppBadge v-if="lesson.data.value.is_completed" kind="success">Пройден</AppBadge>
        <button v-else-if="lesson.data.value.has_access && auth.isStudent" class="btn" :disabled="busy" @click="complete">
          Отметить пройденным
        </button>
        <RouterLink v-if="auth.isTeacher" :to="`/teach/lessons/${id}`" class="btn btn--ghost">Редактировать</RouterLink>
      </PageHeader>

      <div v-if="!lesson.data.value.has_access" class="alert alert--warning" style="margin-bottom: 16px">
        Это бесплатный урок. Чтобы открыть материалы, задания и остальные уроки — запишитесь на курс.
      </div>

      <div class="grid--2" style="align-items: start">
        <div class="stack">
          <section v-if="lesson.data.value.videos.length" class="card stack">
            <div v-if="player" class="video">
              <iframe ref="iframe" :key="player.video_id" :src="withJsApi(player.embed_url)" :title="player.title"
                      allow="accelerometer; autoplay; encrypted-media; gyroscope; picture-in-picture" allowfullscreen />
            </div>
            <p v-if="playerError" class="error">{{ playerError }}</p>
            <ul class="list-plain">
              <li v-for="v in lesson.data.value.videos" :key="v.id" class="row row--between">
                <button class="btn btn--ghost btn--sm btn--wrap" :class="{ active: player?.video_id === v.id }" @click="play(v.id)">
                  ▶ {{ v.title }}
                </button>
                <span class="row small muted">
                  {{ fmtDuration(v.duration_seconds) }}
                  <AppBadge v-if="v.is_completed" kind="success">Просмотрено</AppBadge>
                </span>
              </li>
            </ul>
            <p class="muted small">Видео засчитывается после просмотра 90%.</p>
          </section>

          <LessonComments v-if="lesson.data.value.has_access" :lesson-id="Number(id)" :can-moderate="canModerate" />
        </div>

        <aside class="stack">
          <section v-if="lesson.data.value.materials.length" class="card">
            <h2>Материалы</h2>
            <ul class="list-plain">
              <li v-for="m in lesson.data.value.materials" :key="m.id" class="row row--between">
                <span>{{ m.title }} <span class="muted small">{{ m.file_type }} {{ fmtBytes(m.file_size_bytes) }}</span></span>
                <button v-if="m.has_file" class="btn btn--ghost btn--sm" :disabled="busy" @click="download(m)">Скачать</button>
                <a v-else :href="m.file_url" target="_blank" rel="noopener" class="btn btn--ghost btn--sm">Открыть</a>
              </li>
            </ul>
          </section>

          <section v-if="lesson.data.value.assignments.length" class="card">
            <h2>Домашние задания</h2>
            <ul class="list-plain">
              <li v-for="a in lesson.data.value.assignments" :key="a.id">
                <RouterLink :to="`/assignments/${a.id}`">{{ a.title }}</RouterLink>
                <div class="muted small">до {{ fmtDateTime(a.deadline) }}</div>
              </li>
            </ul>
          </section>

          <section v-if="lesson.data.value.tests.length" class="card">
            <h2>Тесты</h2>
            <ul class="list-plain">
              <li v-for="t in lesson.data.value.tests" :key="t.id">
                <RouterLink :to="`/tests/${t.id}/take`">{{ t.title }}</RouterLink>
                <div class="muted small">{{ testModeLabels[t.mode] }}</div>
              </li>
            </ul>
          </section>
        </aside>
      </div>
    </template>
  </StateBlock>
</template>

<style scoped>
.video {
  position: relative;
  padding-top: 56.25%;
  background: #000;
  border-radius: 8px;
  overflow: hidden;
}
/* YouTube API подменяет iframe — scoped-атрибута у нового элемента нет, поэтому :deep */
.video :deep(iframe) {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border: 0;
}
.active {
  border-color: var(--primary);
}
</style>
