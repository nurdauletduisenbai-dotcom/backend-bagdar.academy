<script setup lang="ts">
import { ref } from 'vue'

import { paymentsApi } from '@/api/payments'
import AppPager from '@/components/ui/AppPager.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAction, useAsync } from '@/composables/useAsync'
import type { Order } from '@/types/api'
import { fmtDate, fmtMoney, orderStatusLabels } from '@/utils/format'

const props = defineProps<{ admin?: boolean }>()
const { act, busy } = useAction()
const status = ref(props.admin ? 'pending' : '')
const page = ref(1)
const list = useAsync(() => paymentsApi.list({ status: status.value || undefined, page: page.value }))
const providerLabel: Record<string, string> = { manual: 'наличные/перевод', stripe: 'карта', kaspi: 'Kaspi' }
const badge: Record<Order['status'], string> = { paid: 'badge--success', pending: 'badge--warning', refunded: '', failed: '' }

function setStatus(s: string) {
  status.value = s
  page.value = 1
  list.run()
}

async function markPaid(o: Order) {
  if (await act(() => paymentsApi.markPaid(o.id), 'Оплата подтверждена — ученик зачислен на курс')) list.run()
}

async function refund(o: Order) {
  if (!confirm('Вернуть деньги и закрыть доступ к курсу?')) return
  if (await act(() => paymentsApi.refund(o.id), 'Возврат оформлен')) list.run()
}

async function cancel(o: Order) {
  if (await act(() => paymentsApi.cancel(o.id), 'Заказ отменён')) list.run()
}
</script>

<template>
  <PageHeader :title="admin ? 'Заказы и оплаты' : 'Мои заказы'"
              :subtitle="admin ? '«Оплачено» = подтверждение оплаты → ученик автоматически зачисляется на курс.' : undefined" />

  <div class="pills" style="margin-bottom: var(--space-lg)">
    <button v-if="admin" class="pill" :class="{ active: status === 'pending' }" @click="setStatus('pending')">Ждут</button>
    <button class="pill" :class="{ active: status === '' }" @click="setStatus('')">Все</button>
    <button class="pill" :class="{ active: status === 'paid' }" @click="setStatus('paid')">Оплачены</button>
    <button class="pill" :class="{ active: status === 'refunded' }" @click="setStatus('refunded')">Возвраты</button>
  </div>

  <StateBlock :loading="list.loading.value" :error="list.error.value" :empty="!list.data.value?.results.length"
              empty-text="Заказов нет" @retry="list.run">
    <div class="stack">
      <article v-for="o in list.data.value?.results ?? []" :key="o.id" class="card order" :class="{ 'card--warning': o.status === 'pending' }">
        <div class="order__info">
          <strong>
            <template v-if="admin">#{{ o.id }} · {{ o.user_email }} → </template>
            <RouterLink :to="`/courses/${o.course}`">{{ o.course_title }}</RouterLink>
          </strong>
          <span class="muted small">
            {{ providerLabel[o.provider] ?? o.provider }} · {{ fmtDate(o.paid_at ?? o.created_at) }}
            <template v-if="!admin && o.status === 'pending' && o.provider === 'manual'"> · ждёт подтверждения администратором</template>
          </span>
        </div>
        <span class="order__amount">{{ fmtMoney(o.amount, o.currency) }}</span>
        <div class="row">
          <a v-if="o.status === 'pending' && o.checkout_url" :href="o.checkout_url" class="btn btn--sm">Оплатить</a>
          <button v-if="admin && o.status === 'pending'" class="btn btn--sm" :disabled="busy" @click="markPaid(o)">Оплачено</button>
          <button v-if="admin && o.status === 'paid'" class="btn btn--ghost btn--sm" :disabled="busy" @click="refund(o)">Возврат</button>
          <button v-if="o.status === 'pending'" class="btn btn--text btn--sm" :disabled="busy" @click="cancel(o)">Отменить</button>
          <span v-if="!(admin && o.status === 'pending')" class="badge" :class="badge[o.status]">{{ orderStatusLabels[o.status] }}</span>
        </div>
      </article>
    </div>
    <AppPager :page="page" :total-pages="list.data.value?.total_pages ?? 1" @change="(p) => { page = p; list.run() }" />
  </StateBlock>
</template>

<style scoped>
.order {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto auto;
  gap: var(--space-lg);
  align-items: center;
  padding: var(--space-md) var(--space-xl);
}
.order__info {
  display: grid;
  gap: 2px;
}
.order__info a {
  color: var(--text-strong);
}
.order__amount {
  font-weight: 600;
  font-variant-numeric: tabular-nums;
}
@media (max-width: 640px) {
  .order {
    grid-template-columns: 1fr;
    gap: var(--space-xs);
  }
}
</style>
