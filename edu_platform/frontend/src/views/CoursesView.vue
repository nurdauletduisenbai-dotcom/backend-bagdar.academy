<script setup lang="ts">
import { reactive } from 'vue'

import { coursesApi } from '@/api/courses'
import CourseCard from '@/components/course/CourseCard.vue'
import AppPager from '@/components/ui/AppPager.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAsync } from '@/composables/useAsync'
import type { CourseType } from '@/types/api'
import { courseTypeLabels } from '@/utils/format'

const filters = reactive({ search: '', type: '' as CourseType | '', page: 1 })
const courses = useAsync(() =>
  coursesApi.list({ search: filters.search || undefined, type: filters.type || undefined, page: filters.page }),
)

function apply() {
  filters.page = 1
  courses.run()
}

function goTo(page: number) {
  filters.page = page
  courses.run()
}
</script>

<template>
  <PageHeader title="Каталог курсов" subtitle="Опубликованные курсы вашей школы" />

  <form class="row" style="margin-bottom: 16px" @submit.prevent="apply">
    <input v-model="filters.search" type="search" placeholder="Поиск по названию или предмету" style="max-width: 320px" />
    <select v-model="filters.type" style="max-width: 220px" @change="apply">
      <option value="">Все типы</option>
      <option v-for="(label, key) in courseTypeLabels" :key="key" :value="key">{{ label }}</option>
    </select>
    <button class="btn btn--ghost">Найти</button>
  </form>

  <StateBlock :loading="courses.loading.value" :error="courses.error.value"
              :empty="!courses.data.value?.results.length" empty-text="Курсы не найдены." @retry="courses.run">
    <div class="grid">
      <CourseCard v-for="c in courses.data.value?.results ?? []" :key="c.id" :course="c" />
    </div>
    <AppPager :page="filters.page" :total-pages="courses.data.value?.total_pages ?? 1" @change="goTo" />
  </StateBlock>
</template>
