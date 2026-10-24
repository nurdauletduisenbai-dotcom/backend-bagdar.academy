<script setup lang="ts">
import AppBadge from '@/components/ui/AppBadge.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import type { Course } from '@/types/api'
import { courseStatusLabels, courseTypeLabels, fmtMoney, subjectTone } from '@/utils/format'

defineProps<{ course: Course; to?: string; showStatus?: boolean; cta?: string }>()
</script>

<template>
  <RouterLink :to="to ?? `/courses/${course.id}`" class="card card--link course-card">
    <div class="course-card__cover" :class="subjectTone(course.subject)">
      <span>{{ (course.subject || course.title).slice(0, 2).toUpperCase() }}</span>
    </div>
    <div class="row">
      <span class="tag" :class="subjectTone(course.subject)">{{ course.subject || courseTypeLabels[course.type] }}</span>
      <AppBadge v-if="showStatus" :kind="course.status === 'published' ? 'success' : 'warning'">
        {{ courseStatusLabels[course.status] }}
      </AppBadge>
    </div>
    <h3 class="course-card__title">{{ course.title }}</h3>
    <span class="course-card__meta">
      {{ courseTypeLabels[course.type] }}<template v-if="course.grade_level"> · {{ course.grade_level }} кл.</template>
    </span>
    <div class="course-card__foot">
      <strong>{{ fmtMoney(course.price) }}</strong>
      <span class="course-card__cta">{{ cta ?? 'Подробнее' }} <AppIcon name="arrow-right" :size="14" /></span>
    </div>
  </RouterLink>
</template>

<style scoped>
.course-card {
  display: flex;
  flex-direction: column;
  gap: var(--space-sm);
  height: 100%;
}
.course-card__cover {
  aspect-ratio: 16 / 8;
  border-radius: var(--radius-md);
  background: linear-gradient(135deg, var(--teal-900), var(--teal-700));
  display: grid;
  place-items: center;
  color: var(--green-500);
  font: 600 var(--fs-h4) / 1 var(--font-sans);
  letter-spacing: 1px;
}
.course-card__cover.tag--purple { background: linear-gradient(135deg, #3c1a86, var(--accent-purple)); color: #fff; }
.course-card__cover.tag--orange { background: linear-gradient(135deg, #b8471d, var(--accent-orange)); color: #fff; }
.course-card__cover.tag--blue { background: linear-gradient(135deg, #1f2b63, var(--accent-blue)); color: #fff; }
.course-card__cover.tag--pink { background: linear-gradient(135deg, #a83b7b, var(--accent-pink)); color: var(--teal-900); }
.course-card__cover.tag--teal { background: linear-gradient(135deg, var(--teal-900), var(--teal-500)); color: #fff; }
.course-card__title {
  font: 600 var(--fs-h5) / var(--lh-h5) var(--font-sans);
  margin: 0;
}
.course-card__meta {
  font: 500 var(--fs-micro) / var(--lh-micro) var(--font-sans);
  color: var(--text-tertiary);
  flex: 1;
}
.course-card__foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: var(--space-sm);
  border-top: 1px solid var(--border-soft);
}
.course-card__cta {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font: 500 var(--fs-body-sm) / 1 var(--font-sans);
  color: var(--text-link);
}
</style>
