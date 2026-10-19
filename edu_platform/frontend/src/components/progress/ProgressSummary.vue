<script setup lang="ts">
import { computed } from 'vue'

import ProgressBar from '@/components/ui/ProgressBar.vue'
import type { CourseReport } from '@/types/api'

/** Плитки + полосы по курсам + столбики баллов тестов (вайрфрейм 2k), по отчётам курсов */
const props = defineProps<{ reports: CourseReport[]; studentId?: number }>()

const lessonsDone = computed(() => props.reports.reduce((n, r) => n + r.lessons_completed_count, 0))
const avgScore = computed(() => {
  const scored = props.reports.filter((r) => r.tests.some((t) => t.best_score_pct !== null))
  return scored.length ? Math.round(scored.reduce((s, r) => s + r.average_test_score, 0) / scored.length) : 0
})
const hwDone = computed(() =>
  props.reports.reduce((n, r) => n + r.assignments.filter((a) => a.status === 'graded' || a.status === 'submitted').length, 0),
)
const attendance = computed(() => {
  let present = 0
  let total = 0
  for (const r of props.reports) {
    for (const [status, n] of Object.entries(r.attendance)) {
      total += n
      if (status === 'present' || status === 'late') present += n
    }
  }
  return total ? Math.round((present / total) * 100) : null
})
const testBars = computed(() =>
  props.reports.flatMap((r) => r.tests.filter((t) => t.best_score_pct !== null).map((t) => ({ title: t.title, value: t.best_score_pct ?? 0 }))),
)
const reportLink = (courseId: number) =>
  props.studentId ? { path: `/progress/courses/${courseId}`, query: { student: props.studentId } } : `/progress/courses/${courseId}`
</script>

<template>
  <div class="stack">
    <div class="kpis">
      <div class="card kpi"><span class="stat">{{ lessonsDone }}</span><span class="muted small">уроков пройдено</span></div>
      <div class="card kpi"><span class="stat">{{ avgScore }}%</span><span class="muted small">ср. балл тестов</span></div>
      <div class="card kpi"><span class="stat">{{ hwDone }}</span><span class="muted small">ДЗ сдано</span></div>
      <div class="card kpi"><span class="stat">{{ attendance === null ? '—' : `${attendance}%` }}</span><span class="muted small">посещаемость</span></div>
    </div>

    <section class="card">
      <h2>Курсы</h2>
      <ul class="list-lines">
        <li v-for="r in reports" :key="r.course_id" class="course-row">
          <RouterLink :to="reportLink(r.course_id)">{{ r.course_title }}</RouterLink>
          <ProgressBar :value="r.percent_completed" />
          <span class="small">{{ r.percent_completed }}% · ср. {{ r.average_test_score }}%</span>
        </li>
      </ul>
    </section>

    <section v-if="testBars.length" class="card">
      <h2>Лучшие результаты тестов</h2>
      <div class="bars">
        <div v-for="(b, i) in testBars" :key="i" class="bar" :title="`${b.title}: ${b.value}%`">
          <span class="bar__value small">{{ Math.round(b.value) }}%</span>
          <div class="bar__fill" :class="{ last: i === testBars.length - 1 }" :style="{ height: `${Math.max(4, b.value)}%` }" />
          <span class="bar__label small muted">{{ b.title }}</span>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
.kpis {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--space-md);
}
.kpi {
  display: grid;
  gap: 2px;
  padding: var(--space-lg);
}
.course-row {
  display: grid;
  grid-template-columns: minmax(0, 1.2fr) minmax(0, 2fr) 120px;
  gap: var(--space-md);
  align-items: center;
}
.bars {
  display: flex;
  gap: var(--space-sm);
  align-items: flex-end;
  height: 180px;
  padding-top: var(--space-md);
}
.bar {
  flex: 1;
  max-width: 90px;
  height: 100%;
  display: grid;
  grid-template-rows: auto 1fr auto;
  gap: 4px;
  text-align: center;
}
.bar__fill {
  align-self: end;
  border-radius: var(--radius-sm) var(--radius-sm) 0 0;
  background: var(--hairline);
}
.bar__fill.last {
  background: var(--green-500);
}
.bar__label {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
@media (max-width: 760px) {
  .kpis {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .course-row {
    grid-template-columns: 1fr;
    gap: 4px;
  }
}
</style>
