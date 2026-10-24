<script setup lang="ts">
import { progressApi } from '@/api/progress'
import ProgressSummary from '@/components/progress/ProgressSummary.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAsync } from '@/composables/useAsync'

const reports = useAsync(async () => {
  const courses = await progressApi.my()
  return Promise.all(courses.map((c) => progressApi.course(c.course_id)))
})
</script>

<template>
  <PageHeader title="Мой прогресс" />
  <StateBlock :loading="reports.loading.value" :error="reports.error.value" :empty="!reports.data.value?.length"
              empty-text="Вы пока не записаны на курсы." @retry="reports.run">
    <ProgressSummary :reports="reports.data.value ?? []" />
  </StateBlock>
</template>
