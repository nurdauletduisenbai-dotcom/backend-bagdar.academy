<script setup lang="ts">
import { useRoute } from 'vue-router'

import { progressApi } from '@/api/progress'
import AppBadge from '@/components/ui/AppBadge.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import ProgressBar from '@/components/ui/ProgressBar.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAsync } from '@/composables/useAsync'
import { attendanceLabels, fmtDateTime, submissionStatusLabels } from '@/utils/format'

const props = defineProps<{ courseId: string }>()
const route = useRoute()
const student = route.query.student ? Number(route.query.student) : undefined
const report = useAsync(() => progressApi.course(Number(props.courseId), student))
</script>

<template>
  <StateBlock :loading="report.loading.value" :error="report.error.value" @retry="report.run">
    <template v-if="report.data.value">
      <PageHeader :title="report.data.value.course_title" subtitle="Отчёт об успеваемости">
        <template #before><RouterLink :to="`/courses/${courseId}`" class="small">← К курсу</RouterLink></template>
      </PageHeader>

      <div class="grid" style="margin-bottom: 16px">
        <div class="card stack" style="gap: 6px">
          <div class="stat">{{ report.data.value.percent_completed }}%</div>
          <ProgressBar :value="report.data.value.percent_completed" />
          <span class="muted small">уроков {{ report.data.value.lessons_completed_count }} из {{ report.data.value.total_lessons_count }}</span>
        </div>
        <div class="card"><div class="stat">{{ report.data.value.average_test_score }}%</div><span class="muted small">средний лучший балл тестов</span></div>
        <div class="card">
          <h3>Посещаемость</h3>
          <span v-for="(n, status) in report.data.value.attendance" :key="status" class="badge" style="margin-right: 6px">
            {{ attendanceLabels[status] }}: {{ n }}
          </span>
          <span v-if="!Object.keys(report.data.value.attendance).length" class="muted small">отметок нет</span>
        </div>
      </div>

      <div class="grid--2" style="align-items: start">
        <section class="card">
          <h2>Уроки</h2>
          <ul class="list-plain">
            <li v-for="l in report.data.value.lessons" :key="l.id" class="row row--between">
              <span>{{ l.title }} <span class="muted small">{{ l.section }}</span></span>
              <AppBadge :kind="l.is_completed ? 'success' : 'default'">{{ l.is_completed ? 'Пройден' : 'Нет' }}</AppBadge>
            </li>
          </ul>
        </section>
        <div class="stack">
          <section class="card">
            <h2>Тесты</h2>
            <p v-if="!report.data.value.tests.length" class="muted small">Тестов нет.</p>
            <ul class="list-plain">
              <li v-for="t in report.data.value.tests" :key="t.id" class="row row--between">
                <span>{{ t.title }} <span class="muted small">попыток: {{ t.attempts }}</span></span>
                <AppBadge :kind="t.passed ? 'success' : t.best_score_pct === null ? 'default' : 'danger'">
                  {{ t.best_score_pct === null ? 'не сдан' : `${t.best_score_pct}%` }}
                </AppBadge>
              </li>
            </ul>
          </section>
          <section class="card">
            <h2>Задания</h2>
            <p v-if="!report.data.value.assignments.length" class="muted small">Заданий нет.</p>
            <ul class="list-plain">
              <li v-for="a in report.data.value.assignments" :key="a.id" class="row row--between">
                <span>{{ a.title }} <span class="muted small">до {{ fmtDateTime(a.deadline) }}</span></span>
                <span class="row">
                  <span v-if="a.score !== null">{{ a.score }}/{{ a.max_score }}</span>
                  <AppBadge :kind="a.status === 'graded' ? 'success' : a.status === 'overdue' ? 'danger' : 'default'">{{ submissionStatusLabels[a.status] }}</AppBadge>
                </span>
              </li>
            </ul>
          </section>
        </div>
      </div>
    </template>
  </StateBlock>
</template>
