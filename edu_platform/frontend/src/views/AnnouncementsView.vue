<script setup lang="ts">
import { reactive, ref } from 'vue'

import { coursesApi } from '@/api/courses'
import { announcementsApi } from '@/api/notifications'
import AppModal from '@/components/ui/AppModal.vue'
import AppPager from '@/components/ui/AppPager.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAction, useAsync } from '@/composables/useAsync'
import { useAuthStore } from '@/stores/auth'
import { fmtDateTime } from '@/utils/format'

const auth = useAuthStore()
const { act, busy } = useAction()
const page = ref(1)
const list = useAsync(() => announcementsApi.list({ page: page.value }))
const courses = useAsync(() => (auth.isTeacher ? coursesApi.list() : Promise.resolve(null)))
const creating = ref(false)
const form = reactive({ title: '', content: '', course: null as number | null, notify: true })

async function create() {
  if (await act(() => announcementsApi.create(form), 'Объявление опубликовано')) {
    creating.value = false
    Object.assign(form, { title: '', content: '' })
    list.run()
  }
}

async function remove(id: number) {
  if (confirm('Удалить объявление?') && (await act(() => announcementsApi.remove(id), 'Удалено'))) list.run()
}
</script>

<template>
  <PageHeader title="Объявления">
    <button v-if="auth.isTeacher" class="btn" @click="creating = true">+ Объявление</button>
  </PageHeader>
  <StateBlock :loading="list.loading.value" :error="list.error.value" :empty="!list.data.value?.results.length"
              empty-text="Объявлений нет." @retry="list.run">
    <div class="stack">
      <article v-for="a in list.data.value?.results ?? []" :key="a.id" class="card">
        <div class="row row--between">
          <h2>{{ a.title }}</h2>
          <button v-if="auth.isTeacher" class="btn btn--ghost btn--sm" @click="remove(a.id)">Удалить</button>
        </div>
        <p style="white-space: pre-line">{{ a.content }}</p>
        <span class="muted small">{{ a.author }} · {{ fmtDateTime(a.created_at) }}{{ a.course ? ' · для курса' : ' · для всей школы' }}</span>
      </article>
    </div>
    <AppPager :page="page" :total-pages="list.data.value?.total_pages ?? 1" @change="(p) => { page = p; list.run() }" />
  </StateBlock>

  <AppModal v-if="creating" title="Новое объявление" @close="creating = false">
    <form class="form" @submit.prevent="create">
      <label>
        Для кого
        <select v-model="form.course">
          <option v-if="auth.isAdmin" :value="null">Вся школа</option>
          <option v-for="c in courses.data.value?.results ?? []" :key="c.id" :value="c.id">Курс: {{ c.title }}</option>
        </select>
      </label>
      <label>Заголовок <input v-model="form.title" required /></label>
      <label>Текст <textarea v-model="form.content" required /></label>
      <label class="inline"><input v-model="form.notify" type="checkbox" /> Разослать уведомления</label>
      <button class="btn" :disabled="busy" style="justify-self: start">Опубликовать</button>
    </form>
  </AppModal>
</template>
