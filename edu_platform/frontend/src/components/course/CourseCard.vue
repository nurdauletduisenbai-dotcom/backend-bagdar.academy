<script setup lang="ts">
import AppBadge from '@/components/ui/AppBadge.vue'
import type { Course } from '@/types/api'
import { courseStatusLabels, courseTypeLabels, fmtMoney } from '@/utils/format'

defineProps<{ course: Course; to?: string; showStatus?: boolean }>()
</script>

<template>
  <RouterLink :to="to ?? `/courses/${course.id}`" class="card card--link stack" style="gap: 8px">
    <div class="row">
      <AppBadge>{{ courseTypeLabels[course.type] }}</AppBadge>
      <AppBadge v-if="showStatus" :kind="course.status === 'published' ? 'success' : 'warning'">
        {{ courseStatusLabels[course.status] }}
      </AppBadge>
    </div>
    <h3>{{ course.title }}</h3>
    <p class="muted small" style="margin: 0">
      {{ course.subject || '—' }}<template v-if="course.grade_level"> · {{ course.grade_level }} класс</template>
    </p>
    <strong>{{ fmtMoney(course.price) }}</strong>
  </RouterLink>
</template>
