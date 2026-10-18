<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { coursesApi, type CoursePayload } from '@/api/courses'
import CourseCard from '@/components/course/CourseCard.vue'
import CourseForm from '@/components/teach/CourseForm.vue'
import AppModal from '@/components/ui/AppModal.vue'
import AppPager from '@/components/ui/AppPager.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAction, useAsync } from '@/composables/useAsync'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()
const { act, busy } = useAction()
const page = ref(1)
const courses = useAsync(() => coursesApi.list({ page: page.value }))
const creating = ref(false)

async function create(payload: CoursePayload) {
  const course = await act(() => coursesApi.create(payload), 'Курс создан')
  if (course) router.push(`/teach/courses/${course.id}`)
}

function goTo(p: number) {
  page.value = p
  courses.run()
}
</script>

<template>
  <PageHeader title="Курсы школы" subtitle="Включая черновики. Редактировать может админ или преподаватель курса.">
    <button v-if="auth.isTeacher" class="btn" @click="creating = true">+ Новый курс</button>
  </PageHeader>

  <StateBlock :loading="courses.loading.value" :error="courses.error.value"
              :empty="!courses.data.value?.results.length" @retry="courses.run">
    <div class="grid">
      <CourseCard v-for="c in courses.data.value?.results ?? []" :key="c.id" :course="c" show-status
                  :to="`/teach/courses/${c.id}`" />
    </div>
    <AppPager :page="page" :total-pages="courses.data.value?.total_pages ?? 1" @change="goTo" />
  </StateBlock>

  <AppModal v-if="creating" title="Новый курс" wide @close="creating = false">
    <CourseForm :busy="busy" @save="create" />
  </AppModal>
</template>
