<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { coursesApi, type CoursePayload } from '@/api/courses'
import CourseAssignmentsTab from '@/components/teach/CourseAssignmentsTab.vue'
import CourseForm from '@/components/teach/CourseForm.vue'
import CourseGroupsTab from '@/components/teach/CourseGroupsTab.vue'
import CourseProgramTab from '@/components/teach/CourseProgramTab.vue'
import CourseStudentsTab from '@/components/teach/CourseStudentsTab.vue'
import CourseTestsTab from '@/components/teach/CourseTestsTab.vue'
import AppBadge from '@/components/ui/AppBadge.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAction, useAsync } from '@/composables/useAsync'
import { courseStatusLabels } from '@/utils/format'

const props = defineProps<{ id: string }>()
const router = useRouter()
const { act, busy } = useAction()
const courseId = Number(props.id)
const course = useAsync(() => coursesApi.get(courseId))

const tabs = { program: 'Программа', tests: 'Тесты', assignments: 'ДЗ', groups: 'Группы', students: 'Ученики', settings: 'Настройки' } as const
const tab = ref<keyof typeof tabs>('program')

async function save(payload: CoursePayload) {
  if (await act(() => coursesApi.update(courseId, payload), 'Курс сохранён')) course.run()
}

async function remove() {
  if (!confirm('Удалить курс? Его можно будет восстановить только через Django admin.')) return
  if (await act(() => coursesApi.remove(courseId), 'Курс удалён')) router.push('/teach/courses')
}
</script>

<template>
  <StateBlock :loading="course.loading.value && !course.data.value" :error="course.error.value" @retry="course.run">
    <template v-if="course.data.value">
      <PageHeader :title="course.data.value.title">
        <template #before><RouterLink to="/teach/courses" class="back small muted">← Курсы</RouterLink></template>
        <AppBadge :kind="course.data.value.status === 'published' ? 'success' : 'warning'">{{ courseStatusLabels[course.data.value.status] }}</AppBadge>
        <RouterLink :to="`/courses/${id}`" class="btn btn--ghost">Как видит ученик</RouterLink>
      </PageHeader>

      <div class="tabs">
        <button v-for="(label, key) in tabs" :key="key" :class="{ active: tab === key }" @click="tab = key">{{ label }}</button>
      </div>

      <CourseProgramTab v-if="tab === 'program'" :course-id="courseId" @tab="(t) => (tab = t as keyof typeof tabs)" />
      <section v-else-if="tab === 'settings'" class="card stack">
        <CourseForm :course="course.data.value" :busy="busy" @save="save" />
        <hr class="divider" />
        <button class="btn btn--danger" style="justify-self: start" :disabled="busy" @click="remove">Удалить курс</button>
      </section>
      <CourseTestsTab v-else-if="tab === 'tests'" :course-id="courseId" />
      <CourseAssignmentsTab v-else-if="tab === 'assignments'" :course-id="courseId" />
      <CourseGroupsTab v-else-if="tab === 'groups'" :course-id="courseId" />
      <CourseStudentsTab v-else :course-id="courseId" />
    </template>
  </StateBlock>
</template>
