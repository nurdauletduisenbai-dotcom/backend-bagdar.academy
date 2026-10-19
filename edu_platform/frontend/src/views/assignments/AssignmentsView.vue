<script setup lang="ts">
import { computed } from 'vue'

import { assignmentsApi } from '@/api/assignments'
import PageHeader from '@/components/ui/PageHeader.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAsync } from '@/composables/useAsync'
import { useAuthStore } from '@/stores/auth'
import type { Assignment } from '@/types/api'
import { fmtDateTime } from '@/utils/format'

const auth = useAuthStore()
const list = useAsync(() => assignmentsApi.list())
const items = computed(() => list.data.value?.results ?? [])

/** Доска по статусам (вайрфрейм 2h) */
const columns = computed(() => {
  const todo: Assignment[] = []
  const review: Assignment[] = []
  const graded: Assignment[] = []
  for (const a of items.value) {
    const s = a.my_submission?.status
    if (!s || s === 'returned') todo.push(a)
    else if (s === 'submitted') review.push(a)
    else graded.push(a)
  }
  return [
    { key: 'todo', title: 'Нужно сдать', items: todo },
    { key: 'review', title: 'На проверке', items: review },
    { key: 'graded', title: 'Проверено', items: graded },
  ]
})

function cardClass(a: Assignment) {
  if (a.my_submission?.status === 'returned') return 'card--returned'
  if (!a.my_submission && a.is_overdue) return 'card--overdue'
  if (!a.my_submission && new Date(a.deadline).getTime() - Date.now() < 86400_000) return 'card--warning'
  return ''
}
</script>

<template>
  <PageHeader title="Задания">
    <RouterLink v-if="auth.isTeacher" to="/teach/submissions" class="btn">Проверка работ</RouterLink>
  </PageHeader>

  <StateBlock :loading="list.loading.value" :error="list.error.value" :empty="!items.length" empty-text="Заданий нет" @retry="list.run">
    <!-- Ученик: доска -->
    <div v-if="auth.isStudent" class="board">
      <section v-for="col in columns" :key="col.key" class="board__col">
        <div class="board__head"><strong>{{ col.title }}</strong> <span class="muted">· {{ col.items.length }}</span></div>
        <RouterLink v-for="a in col.items" :key="a.id" :to="`/assignments/${a.id}`" class="card card--link task" :class="cardClass(a)">
          <strong>{{ a.title }}</strong>
          <span class="small muted">
            <template v-if="a.my_submission?.status === 'graded'">{{ a.my_submission.score }}/{{ a.max_score }}<template v-if="a.my_submission.feedback"> · есть комментарий</template></template>
            <template v-else-if="a.my_submission?.status === 'returned'">на доработку</template>
            <template v-else-if="a.my_submission">сдано {{ fmtDateTime(a.my_submission.submitted_at) }}</template>
            <template v-else>{{ a.is_overdue ? 'просрочено · ' : 'до ' }}{{ fmtDateTime(a.deadline) }}</template>
          </span>
        </RouterLink>
        <p v-if="!col.items.length" class="muted small empty">пусто</p>
      </section>
    </div>

    <!-- Учитель / админ: таблица -->
    <div v-else class="card card--flush table-wrap">
      <table class="table">
        <thead><tr><th>Задание</th><th>Дедлайн</th><th>Сдач</th><th></th></tr></thead>
        <tbody>
          <tr v-for="a in items" :key="a.id">
            <td><RouterLink :to="`/assignments/${a.id}`">{{ a.title }}</RouterLink></td>
            <td :class="{ error: a.is_overdue }">{{ fmtDateTime(a.deadline) }}</td>
            <td>{{ a.submissions_count ?? 0 }}</td>
            <td><RouterLink :to="{ path: '/teach/submissions', query: { assignment: a.id } }" class="btn btn--ghost btn--sm">Проверить</RouterLink></td>
          </tr>
        </tbody>
      </table>
    </div>
  </StateBlock>
</template>

<style scoped>
.board {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--space-md);
  align-items: start;
}
.board__col {
  display: grid;
  gap: var(--space-sm);
  padding: var(--space-md);
  border-radius: var(--radius-lg);
  background: var(--surface-subtle);
}
.board__head {
  padding: 0 4px;
}
.task {
  display: grid;
  gap: 4px;
  padding: var(--space-md);
}
.card--overdue,
.card--returned {
  border-color: #f0b8b3;
}
.card--returned .small {
  color: var(--error-text);
}
.empty {
  margin: 0;
  text-align: center;
}
@media (max-width: 860px) {
  .board {
    grid-template-columns: 1fr;
  }
}
</style>
