<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { coursesApi } from '@/api/courses'
import { errorMessage } from '@/api/http'
import type { Course } from '@/types/api'

const typeLabels: Record<Course['type'], string> = {
  school_subject: 'Школьный предмет',
  exam_prep: 'Подготовка к экзамену',
  club: 'Кружок',
}

const courses = ref<Course[]>([])
const search = ref('')
const loading = ref(false)
const error = ref('')

async function load() {
  loading.value = true
  error.value = ''
  try {
    const page = await coursesApi.list({ search: search.value || undefined })
    courses.value = page.results
  } catch (e) {
    error.value = errorMessage(e)
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <section>
    <div class="toolbar">
      <h1>Курсы</h1>
      <form @submit.prevent="load">
        <input v-model="search" type="search" placeholder="Поиск курса" />
      </form>
    </div>

    <p v-if="loading">Загрузка…</p>
    <p v-else-if="error" class="error">{{ error }}</p>
    <p v-else-if="!courses.length">Курсов пока нет.</p>

    <ul v-else class="grid">
      <li v-for="course in courses" :key="course.id" class="card">
        <span class="badge">{{ typeLabels[course.type] }}</span>
        <h2>{{ course.title }}</h2>
        <p class="muted">
          {{ course.subject }}<template v-if="course.grade_level"> · {{ course.grade_level }} класс</template>
        </p>
        <p>{{ Number(course.price) > 0 ? `${course.price} ₸` : 'Бесплатно' }}</p>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
}
.grid {
  list-style: none;
  padding: 0;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
}
h2 {
  font-size: 18px;
  margin: 8px 0 4px;
}
</style>
