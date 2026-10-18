<script setup lang="ts">
import { computed, ref } from 'vue'

import { coursesApi } from '@/api/courses'
import { paymentsApi } from '@/api/payments'
import AppBadge from '@/components/ui/AppBadge.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
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

const course = useAsync(() => coursesApi.get(Number(props.id)))
const providers = useAsync(() => paymentsApi.providers())
const provider = ref<Order['provider']>('manual')
const isFree = computed(() => Number(course.data.value?.price ?? 0) <= 0)
const canBuy = computed(() => !course.data.value?.is_enrolled && auth.hasRole('student', 'parent'))

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
      <PageHeader :title="course.data.value.title" :subtitle="courseTypeLabels[course.data.value.type]">
        <template #before><RouterLink to="/catalog" class="small">← Каталог</RouterLink></template>
        <RouterLink v-if="auth.isStaff" :to="`/teach/courses/${id}`" class="btn btn--ghost">Редактировать</RouterLink>
        <RouterLink v-if="course.data.value.is_enrolled" :to="`/progress/courses/${id}`" class="btn btn--ghost">Мой прогресс</RouterLink>
      </PageHeader>

      <div class="grid--2" style="align-items: start">
        <div class="stack">
          <section class="card">
            <p style="white-space: pre-line; margin-top: 0">{{ course.data.value.description || 'Описание пока не добавлено.' }}</p>
            <p class="muted small">
              {{ course.data.value.subject }}<template v-if="course.data.value.grade_level"> · {{ course.data.value.grade_level }} класс</template>
              · доступ {{ course.data.value.access_days }} дней
            </p>
          </section>

          <section v-for="section in course.data.value.sections" :key="section.id" class="card">
            <h2>{{ section.title }}</h2>
            <ul class="list-plain">
              <li v-for="lesson in section.lessons" :key="lesson.id" class="row row--between">
                <RouterLink :to="`/lessons/${lesson.id}`">{{ lesson.title }}</RouterLink>
                <span class="row small muted">
                  <span v-for="v in lesson.videos" :key="v.id">▶ {{ fmtDuration(v.duration_seconds) }}</span>
                  <AppBadge v-if="lesson.is_free_preview" kind="info">Бесплатно</AppBadge>
                  <AppBadge v-if="!lesson.is_published" kind="warning">Не опубликован</AppBadge>
                </span>
              </li>
            </ul>
            <p v-if="!section.lessons.length" class="muted small">Уроков пока нет.</p>
          </section>
          <p v-if="!course.data.value.sections.length" class="muted">Программа курса пока пустая.</p>
        </div>

        <aside class="stack">
          <section class="card stack">
            <strong class="stat">{{ fmtMoney(course.data.value.price) }}</strong>
            <AppBadge v-if="course.data.value.is_enrolled" kind="success">Вы записаны</AppBadge>
            <template v-else-if="canBuy">
              <label v-if="!isFree">
                Способ оплаты
                <select v-model="provider">
                  <option v-for="p in providers.data.value ?? []" :key="p.name" :value="p.name" :disabled="!p.is_configured">
                    {{ { manual: 'Наличные / перевод (подтверждает админ)', stripe: 'Карта (Stripe)', kaspi: 'Kaspi Pay' }[p.name] ?? p.name }}
                    {{ p.is_configured ? '' : '— не настроено' }}
                  </option>
                </select>
              </label>
              <button class="btn" :disabled="busy" @click="enroll">{{ isFree ? 'Записаться бесплатно' : 'Купить курс' }}</button>
            </template>
            <p v-else-if="!course.data.value.is_enrolled" class="muted small">Записаться может ученик или родитель.</p>
          </section>

          <section v-if="course.data.value.tests.length" class="card">
            <h2>Тесты</h2>
            <ul class="list-plain">
              <li v-for="t in course.data.value.tests" :key="t.id" class="stack" style="gap: 4px">
                <RouterLink :to="`/tests/${t.id}/take`">{{ t.title }}</RouterLink>
                <span class="small muted">
                  {{ testModeLabels[t.mode] }} · {{ t.time_limit_minutes ? `${t.time_limit_minutes} мин` : 'без таймера' }}
                  · попыток: {{ t.max_attempts || '∞' }}
                </span>
              </li>
            </ul>
          </section>
        </aside>
      </div>
    </template>
  </StateBlock>
</template>
