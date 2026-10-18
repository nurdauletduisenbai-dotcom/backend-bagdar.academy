<script setup lang="ts">
import { progressApi } from '@/api/progress'
import PageHeader from '@/components/ui/PageHeader.vue'
import ProgressBar from '@/components/ui/ProgressBar.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAsync } from '@/composables/useAsync'
import { enrollmentStatusLabels, fmtDate } from '@/utils/format'

const list = useAsync(() => progressApi.my())
</script>

<template>
  <PageHeader title="Мой прогресс" />
  <StateBlock :loading="list.loading.value" :error="list.error.value" :empty="!list.data.value?.length" @retry="list.run">
    <div class="card table-wrap">
      <table class="table">
        <thead><tr><th>Курс</th><th style="width: 220px">Пройдено</th><th>Ср. балл тестов</th><th>Доступ</th><th></th></tr></thead>
        <tbody>
          <tr v-for="c in list.data.value ?? []" :key="c.course_id">
            <td><RouterLink :to="`/courses/${c.course_id}`">{{ c.course_title }}</RouterLink></td>
            <td><ProgressBar :value="c.percent_completed" /> <span class="small">{{ c.percent_completed }}%</span></td>
            <td>{{ c.average_test_score }}%</td>
            <td>{{ enrollmentStatusLabels[c.enrollment_status] }} до {{ fmtDate(c.access_until) }}</td>
            <td><RouterLink :to="`/progress/courses/${c.course_id}`" class="btn btn--ghost btn--sm">Подробно</RouterLink></td>
          </tr>
        </tbody>
      </table>
    </div>
  </StateBlock>
</template>
