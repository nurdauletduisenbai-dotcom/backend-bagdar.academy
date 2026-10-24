<script setup lang="ts">
import { computed, ref } from 'vue'

import { coursesApi } from '@/api/courses'
import { paymentsApi } from '@/api/payments'
import { progressApi } from '@/api/progress'
import AppIcon from '@/components/ui/AppIcon.vue'
import ProgressBar from '@/components/ui/ProgressBar.vue'
import ProgressRing from '@/components/ui/ProgressRing.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAction, useAsync } from '@/composables/useAsync'
import { useAuthStore } from '@/stores/auth'
import { useToast } from '@/stores/toast'
import type { Order } from '@/types/api'
import { courseTypeLabels, fmtDuration, fmtMoney, testModeLabels } from '@/utils/format'

const props = defineProps<{ id: string }>()
const auth = useAuthStore()
const toast = useToast()
const { act, busy } = useAction()

const course = useAsync(async () => {
  const c = await coursesApi.get(Number(props.id))
  if (c.is_enrolled && auth.isStudent) report.run()
  return c
})
const report = useAsync(() => progressApi.course(Number(props.id)), { immediate: false })
const providers = useAsync(() => paymentsApi.providers())
const provider = ref<Order['provider']>('manual')
const openSections = ref<Record<number, boolean>>({ 0: true })

const isFree = computed(() => Number(course.data.value?.price ?? 0) <= 0)
const canBuy = computed(() => !course.data.value?.is_enrolled && auth.hasRole('student', 'parent'))
const lessonsCount = computed(() => course.data.value?.sections.reduce((n, s) => n + s.lessons.length, 0) ?? 0)
const hasPreview = computed(() => course.data.value?.sections.some((s) => s.lessons.some((l) => l.is_free_preview)))
const nextLesson = computed(() => report.data.value?.lessons.find((l) => !l.is_completed) ?? null)
const providerLabel: Record<string, string> = { manual: 'Наличные / перевод', stripe: 'Карта (Stripe)', kaspi: 'Kaspi Pay' }

/** Прогресс по разделу из отчёта (уроки отчёта несут название раздела) */
function sectionProgress(title: string) {
  const lessons = report.data.value?.lessons.filter((l) => l.section === title) ?? []
  return lessons.length ? Math.round((lessons.filter((l) => l.is_completed).length / lessons.length) * 100) : 0
}
const done = (lessonId: number) => report.data.value?.lessons.find((l) => l.id === lessonId)?.is_completed ?? false

async function enroll() {
  const order = await act(() => paymentsApi.create(Number(props.id), isFree.value ? 'manual' : provider.value))
  if (!order) return
  if (order.status === 'paid') {
    toast.success('Вы записаны на курс')
    course.run()
  } else if (order.checkout_url) {
    window.location.href = order.checkout_url
  } else {
    toast.info('Заказ создан и ждёт подтверждения оплаты администратором. Статус — в «Мои заказы».')
  }
}
</script>

<template>
  <StateBlock :loading="course.loading.value" :error="course.error.value" @retry="course.run">
    <template v-if="course.data.value">
      <!-- ====== Записан (вайрфрейм 1k) ====== -->
      <template v-if="course.data.value.is_enrolled">
        <div class="row row--between head">
          <div>
            <RouterLink to="/my-courses" class="back small muted"><AppIcon name="arrow-left" :size="14" /> Мои курсы</RouterLink>
            <h1>{{ course.data.value.title }}</h1>
          </div>
          <div class="row">
            <RouterLink v-if="auth.isStaff" :to="`/teach/courses/${id}`" class="btn btn--ghost">Редактировать</RouterLink>
            <RouterLink :to="`/progress/courses/${id}`" class="btn btn--ghost">Мой прогресс</RouterLink>
          </div>
        </div>

        <section v-if="auth.isStudent" class="card next">
          <ProgressRing :value="report.data.value?.percent_completed ?? 0" :size="96" />
          <div class="next__body">
            <div class="eyebrow">Далее</div>
            <h2 class="next__title">{{ nextLesson?.title ?? 'Все уроки пройдены' }}</h2>
            <RouterLink v-if="nextLesson" :to="`/lessons/${nextLesson.id}`" class="btn">Продолжить</RouterLink>
          </div>
          <div v-if="report.data.value" class="pills next__chips">
            <span class="pill">Тесты {{ report.data.value.tests.filter((t) => t.passed).length }}/{{ report.data.value.tests.length }}</span>
            <span class="pill">ДЗ {{ report.data.value.assignments.filter((a) => a.status === 'graded' || a.status === 'submitted').length }}/{{ report.data.value.assignments.length }}</span>
          </div>
        </section>
      </template>

      <!-- ====== Лендинг (вайрфрейм 1j) ====== -->
      <section v-else class="band page-band landing">
        <div class="landing__info">
          <RouterLink to="/catalog" class="back small muted"><AppIcon name="arrow-left" :size="14" /> Каталог</RouterLink>
          <div class="eyebrow">
            {{ course.data.value.subject || courseTypeLabels[course.data.value.type] }}<template v-if="course.data.value.grade_level"> · {{ course.data.value.grade_level }} класс</template>
          </div>
          <h1 class="landing__title">{{ course.data.value.title }}</h1>
          <p class="muted">{{ lessonsCount }} уроков · {{ course.data.value.tests.length }} тестов · доступ {{ course.data.value.access_days }} дней</p>
          <p v-if="course.data.value.description" class="landing__desc">{{ course.data.value.description }}</p>
          <RouterLink v-if="auth.isStaff" :to="`/teach/courses/${id}`" class="btn btn--ghost btn--sm" style="justify-self: start">Редактировать</RouterLink>
        </div>
        <aside class="card price">
          <span class="stat">{{ fmtMoney(course.data.value.price) }}</span>
          <template v-if="canBuy">
            <select v-if="!isFree" v-model="provider" aria-label="Способ оплаты">
              <option v-for="p in providers.data.value ?? []" :key="p.name" :value="p.name" :disabled="!p.is_configured">
                {{ providerLabel[p.name] ?? p.name }}{{ p.is_configured ? '' : ' — не настроено' }}
              </option>
            </select>
            <button class="btn btn--block" :disabled="busy" @click="enroll">{{ isFree ? 'Записаться бесплатно' : 'Купить курс' }}</button>
          </template>
          <p v-else class="muted small">Записаться может ученик или родитель.</p>
          <p v-if="hasPreview" class="muted small center">первый урок бесплатно</p>
        </aside>
      </section>

      <div class="layout">
        <section class="stack">
          <h2>Программа</h2>
          <article v-for="(section, i) in course.data.value.sections" :key="section.id" class="card section">
            <button class="section__head" @click="openSections[i] = !openSections[i]">
              <span class="row">
                <AppIcon :name="openSections[i] ? 'chevron-down' : 'chevron-right'" :size="16" />
                <strong>{{ section.title }}</strong>
                <span class="muted small">· {{ section.lessons.length }} уроков</span>
              </span>
              <span v-if="report.data.value" class="section__bar"><ProgressBar :value="sectionProgress(section.title)" /></span>
            </button>
            <ul v-if="openSections[i]" class="list-lines section__lessons">
              <li v-for="lesson in section.lessons" :key="lesson.id" class="lesson-row">
                <AppIcon :name="done(lesson.id) ? 'check' : (course.data.value.is_enrolled || lesson.is_free_preview) ? 'play' : 'lock'" :size="14"
                         :class="{ ok: done(lesson.id) }" />
                <RouterLink v-if="course.data.value.is_enrolled || lesson.is_free_preview || auth.isStaff" :to="`/lessons/${lesson.id}`">{{ lesson.title }}</RouterLink>
                <span v-else class="muted">{{ lesson.title }}</span>
                <span class="row small muted">
                  <span v-if="lesson.is_free_preview" class="badge badge--success">Бесплатно</span>
                  <span v-if="!lesson.is_published" class="badge badge--warning">Не опубликован</span>
                  <span v-for="v in lesson.videos" :key="v.id">{{ fmtDuration(v.duration_seconds) }}</span>
                </span>
              </li>
            </ul>
          </article>
          <p v-if="!course.data.value.sections.length" class="muted">Программа курса пока пустая.</p>
        </section>

        <aside v-if="course.data.value.tests.length" class="card tests">
          <h2>Тесты</h2>
          <ul class="list-lines">
            <li v-for="t in course.data.value.tests" :key="t.id" class="stack" style="gap: 2px">
              <RouterLink :to="`/tests/${t.id}/take`">{{ t.title }}</RouterLink>
              <span class="small muted">
                {{ testModeLabels[t.mode] }} · {{ t.time_limit_minutes ? `${t.time_limit_minutes} мин` : 'без таймера' }} · попыток {{ t.max_attempts || '∞' }}
              </span>
            </li>
          </ul>
        </aside>
      </div>
    </template>
  </StateBlock>
</template>

<style scoped>
.back {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}
.head {
  align-items: flex-end;
  margin-bottom: var(--space-xl);
}
.next {
  display: flex;
  align-items: center;
  gap: var(--space-xl);
  margin-bottom: var(--space-xl);
  flex-wrap: wrap;
}
.next__body {
  display: grid;
  gap: var(--space-xs);
  flex: 1;
  justify-items: start;
}
.next__title {
  font: 500 var(--fs-h4) / var(--lh-h4) var(--font-sans);
  margin: 0;
}
.next__chips .pill {
  cursor: default;
}
.landing {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 300px;
  gap: var(--space-xxl);
  align-items: center;
  padding-top: var(--space-xxxl);
  padding-bottom: var(--space-xxxl);
}
.landing__info {
  display: grid;
  gap: var(--space-sm);
}
.landing__info p {
  margin: 0;
}
.landing__title {
  font: 500 var(--fs-h1) / var(--lh-h1) var(--font-sans);
  letter-spacing: -0.5px;
}
.landing__desc {
  color: var(--text-on-dark-muted);
  max-width: 640px;
  white-space: pre-line;
}
.price {
  display: grid;
  gap: var(--space-sm);
  color: var(--text-body);
  box-shadow: var(--shadow-3);
}
.price p {
  margin: 0;
}
.center {
  text-align: center;
}
.layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) 320px;
  gap: var(--space-xl);
  align-items: start;
}
.section {
  padding: 0;
}
.section__head {
  width: 100%;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-md);
  padding: var(--space-md) var(--space-lg);
  background: none;
  border: 0;
  cursor: pointer;
  font: inherit;
  color: inherit;
  text-align: left;
}
.section__bar {
  width: 160px;
}
.section__lessons {
  padding: 0 var(--space-lg) var(--space-sm);
}
.lesson-row {
  display: grid;
  grid-template-columns: 18px minmax(0, 1fr) auto;
  gap: var(--space-sm);
  align-items: center;
}
.ok {
  color: var(--green-600);
}
@media (max-width: 960px) {
  .layout,
  .landing {
    grid-template-columns: 1fr;
  }
}
</style>
