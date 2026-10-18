<script setup lang="ts">
import { computed, ref } from 'vue'

import { commentsApi } from '@/api/content'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAction, useAsync } from '@/composables/useAsync'
import { useAuthStore } from '@/stores/auth'
import type { Comment } from '@/types/api'
import { fmtDateTime } from '@/utils/format'

const props = defineProps<{ lessonId: number; canModerate: boolean }>()
const auth = useAuthStore()
const { act, busy } = useAction()

const comments = useAsync(() => commentsApi.list(props.lessonId))
const text = ref('')
const replyTo = ref<Comment | null>(null)

const roots = computed(() => (comments.data.value?.results ?? []).filter((c) => !c.parent))
const repliesOf = (id: number) => (comments.data.value?.results ?? []).filter((c) => c.parent === id)

async function send() {
  if (!text.value.trim()) return
  const ok = await act(() => commentsApi.create({ lesson: props.lessonId, content: text.value, parent: replyTo.value?.id }))
  if (ok) {
    text.value = ''
    replyTo.value = null
    comments.run()
  }
}

async function remove(c: Comment) {
  await act(() => commentsApi.remove(c.id), 'Комментарий удалён')
  comments.run()
}

async function toggle(c: Comment) {
  await act(() => commentsApi.toggleHidden(c.id))
  comments.run()
}
</script>

<template>
  <section class="card">
    <h2>Вопросы и обсуждение</h2>
    <StateBlock :loading="comments.loading.value" :error="comments.error.value" :empty="!roots.length"
                empty-text="Пока нет вопросов — задайте первый." @retry="comments.run">
      <ul class="list-plain">
        <li v-for="c in roots" :key="c.id" class="stack" style="gap: 6px">
          <div class="row row--between">
            <strong>{{ c.author.name }}</strong>
            <span class="muted small">{{ fmtDateTime(c.created_at) }}</span>
          </div>
          <p style="margin: 0; white-space: pre-line" :class="{ muted: c.is_hidden }">
            {{ c.content }} <span v-if="c.is_hidden" class="badge">скрыт</span>
          </p>
          <div class="row small">
            <button class="btn btn--ghost btn--sm" @click="replyTo = c">Ответить</button>
            <button v-if="c.author.id === auth.user?.id || canModerate" class="btn btn--ghost btn--sm" @click="remove(c)">Удалить</button>
            <button v-if="canModerate" class="btn btn--ghost btn--sm" @click="toggle(c)">{{ c.is_hidden ? 'Показать' : 'Скрыть' }}</button>
          </div>
          <ul v-if="repliesOf(c.id).length" class="list-plain" style="margin-left: 24px">
            <li v-for="r in repliesOf(c.id)" :key="r.id">
              <div class="row row--between">
                <strong>{{ r.author.name }}</strong>
                <span class="muted small">{{ fmtDateTime(r.created_at) }}</span>
              </div>
              <p style="margin: 4px 0 0; white-space: pre-line">{{ r.content }}</p>
              <button v-if="r.author.id === auth.user?.id || canModerate" class="btn btn--ghost btn--sm" @click="remove(r)">Удалить</button>
            </li>
          </ul>
        </li>
      </ul>
    </StateBlock>

    <form class="form" style="margin-top: 16px" @submit.prevent="send">
      <p v-if="replyTo" class="small">
        Ответ для <strong>{{ replyTo.author.name }}</strong>
        <button type="button" class="btn btn--ghost btn--sm" @click="replyTo = null">отмена</button>
      </p>
      <textarea v-model="text" placeholder="Ваш вопрос или комментарий" required />
      <button class="btn" :disabled="busy" style="justify-self: start">Отправить</button>
    </form>
  </section>
</template>
