<script setup lang="ts">
import { computed, reactive, ref } from 'vue'

import { coursesApi } from '@/api/courses'
import CourseCard from '@/components/course/CourseCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppPager from '@/components/ui/AppPager.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAsync } from '@/composables/useAsync'
import type { CourseType } from '@/types/api'
import { courseTypeLabels } from '@/utils/format'

const filters = reactive({ search: '', type: '' as CourseType | '', subject: '', page: 1 })
const subjects = ref<string[]>([])
const courses = useAsync(async () => {
  const data = await coursesApi.list({
    search: filters.search || undefined, type: filters.type || undefined,
    subject: filters.subject || undefined, page: filters.page,
  })
  // Предметы-пилюли собираем из каталога без фильтра предмета
  if (!filters.subject && !filters.search) {
    subjects.value = [...new Set([...subjects.value, ...data.results.map((c) => c.subject).filter(Boolean)])]
  }
  return data
})
const total = computed(() => courses.data.value?.total ?? 0)

function apply() {
  filters.page = 1
  courses.run()
}

function pickSubject(s: string) {
  filters.subject = s
  apply()
}
</script>

<template>
  <section class="band page-band catalog-band">
    <h1>Каталог курсов</h1>
    <form class="search" @submit.prevent="apply">
      <AppIcon name="search" />
      <input v-model="filters.search" type="search" placeholder="Поиск: алгебра, ЕНТ, олимпиада…" aria-label="Поиск курсов" />
    </form>
  </section>

  <div class="row row--between filters">
    <div class="pills">
      <button class="pill" :class="{ active: !filters.subject }" @click="pickSubject('')">Все</button>
      <button v-for="s in subjects" :key="s" class="pill" :class="{ active: filters.subject === s }" @click="pickSubject(s)">{{ s }}</button>
    </div>
    <select v-model="filters.type" class="type-select" aria-label="Тип курса" @change="apply">
      <option value="">Все типы</option>
      <option v-for="(label, key) in courseTypeLabels" :key="key" :value="key">{{ label }}</option>
    </select>
  </div>

  <p class="muted small">{{ total }} {{ total === 1 ? 'курс' : 'курсов' }}</p>

  <StateBlock :loading="courses.loading.value" :error="courses.error.value"
              :empty="!courses.data.value?.results.length" empty-text="Курсы не найдены — попробуйте другой запрос." @retry="courses.run">
    <div class="grid">
      <CourseCard v-for="c in courses.data.value?.results ?? []" :key="c.id" :course="c" />
    </div>
    <AppPager :page="filters.page" :total-pages="courses.data.value?.total_pages ?? 1" @change="(p) => { filters.page = p; courses.run() }" />
  </StateBlock>
</template>

<style scoped>
.catalog-band {
  display: grid;
  gap: var(--space-lg);
}
.catalog-band .search {
  max-width: 640px;
  border-color: transparent;
}
.filters {
  margin-bottom: var(--space-sm);
}
.type-select {
  width: auto;
  min-width: 200px;
}
</style>
