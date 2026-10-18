<script setup lang="ts">
import { computed } from 'vue'

import { progressApi } from '@/api/progress'
import PageHeader from '@/components/ui/PageHeader.vue'
import ProgressBar from '@/components/ui/ProgressBar.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAsync } from '@/composables/useAsync'
import { fmtDate } from '@/utils/format'

const progress = useAsync(() => progressApi.my())
const active = computed(() => (progress.data.value ?? []).filter((c) => c.enrollment_status === 'active'))
</script>

<template>
  <PageHeader title="Мои курсы">
    <RouterLink to="/catalog" class="btn btn--ghost">Каталог</RouterLink>
  </PageHeader>
  <StateBlock :loading="progress.loading.value" :error="progress.error.value" :empty="!active.length"
              empty-text="Вы пока не записаны ни на один курс." @retry="progress.run">
    <div class="grid">
      <RouterLink v-for="c in active" :key="c.course_id" :to="`/courses/${c.course_id}`" class="card card--link stack" style="gap: 8px">
        <h3>{{ c.course_title }}</h3>
        <ProgressBar :value="c.percent_completed" />
        <span class="small muted">Пройдено {{ c.percent_completed }}% · средний балл тестов {{ c.average_test_score }}%</span>
        <span class="small muted">Доступ до {{ fmtDate(c.access_until) }}</span>
      </RouterLink>
    </div>
  </StateBlock>
</template>
