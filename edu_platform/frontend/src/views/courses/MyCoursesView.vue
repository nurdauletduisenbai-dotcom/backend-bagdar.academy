<script setup lang="ts">
import { computed, ref } from 'vue'

import { progressApi } from '@/api/progress'
import PageHeader from '@/components/ui/PageHeader.vue'
import ProgressBar from '@/components/ui/ProgressBar.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAsync } from '@/composables/useAsync'
import { fmtDate } from '@/utils/format'

const progress = useAsync(() => progressApi.my())
const tab = ref<'active' | 'done'>('active')
const daysLeft = (iso: string) => Math.ceil((new Date(iso).getTime() - Date.now()) / 86400_000)

const active = computed(() => (progress.data.value ?? []).filter((c) => c.enrollment_status === 'active' && c.percent_completed < 100))
const done = computed(() => (progress.data.value ?? []).filter((c) => c.enrollment_status !== 'active' || c.percent_completed >= 100))
const list = computed(() => (tab.value === 'active' ? active.value : done.value))
</script>

<template>
  <PageHeader title="Мои курсы">
    <div class="pills">
      <button class="pill" :class="{ active: tab === 'active' }" @click="tab = 'active'">Активные <span class="count">{{ active.length }}</span></button>
      <button class="pill" :class="{ active: tab === 'done' }" @click="tab = 'done'">Завершённые <span class="count">{{ done.length }}</span></button>
    </div>
  </PageHeader>

  <StateBlock :loading="progress.loading.value" :error="progress.error.value" :empty="!list.length"
              :empty-text="tab === 'active' ? 'Активных курсов нет — загляните в каталог.' : 'Завершённых курсов пока нет.'" @retry="progress.run">
    <div class="stack">
      <article v-for="c in list" :key="c.course_id" class="card my-course"
               :class="{ 'card--warning': c.enrollment_status === 'active' && daysLeft(c.access_until) <= 7 }">
        <div class="my-course__info">
          <RouterLink :to="`/courses/${c.course_id}`" class="my-course__title">{{ c.course_title }}</RouterLink>
          <span class="muted small">
            <template v-if="c.enrollment_status === 'active' && daysLeft(c.access_until) <= 7">
              доступ заканчивается через {{ daysLeft(c.access_until) }} дн.
            </template>
            <template v-else>средний балл тестов {{ c.average_test_score }}% · доступ до {{ fmtDate(c.access_until) }}</template>
          </span>
        </div>
        <div class="my-course__bar"><ProgressBar :value="c.percent_completed" /><span class="small">{{ c.percent_completed }}%</span></div>
        <RouterLink :to="`/courses/${c.course_id}`" class="btn btn--sm" :class="{ 'btn--ghost': c.percent_completed >= 100 }">
          {{ c.percent_completed >= 100 ? 'Повторить' : 'Продолжить' }}
        </RouterLink>
      </article>
    </div>
  </StateBlock>
  <RouterLink to="/catalog" class="btn btn--ghost" style="margin-top: var(--space-xl)">+ Найти курс в каталоге</RouterLink>
</template>

<style scoped>
.my-course {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(140px, 220px) auto;
  gap: var(--space-xl);
  align-items: center;
  padding: var(--space-lg) var(--space-xl);
}
.my-course__info {
  display: grid;
  gap: 2px;
}
.my-course__title {
  font: 600 var(--fs-h5) / var(--lh-h5) var(--font-sans);
  color: var(--text-strong);
}
.my-course__bar {
  display: grid;
  grid-template-columns: 1fr 40px;
  gap: var(--space-sm);
  align-items: center;
}
@media (max-width: 640px) {
  .my-course {
    grid-template-columns: 1fr;
    gap: var(--space-sm);
  }
}
</style>
