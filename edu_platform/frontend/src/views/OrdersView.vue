<script setup lang="ts">
import { ref } from 'vue'

import { paymentsApi } from '@/api/payments'
import AppBadge from '@/components/ui/AppBadge.vue'
import AppPager from '@/components/ui/AppPager.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAction, useAsync } from '@/composables/useAsync'
import type { Order } from '@/types/api'
import { fmtDateTime, fmtMoney, orderStatusLabels } from '@/utils/format'

const props = defineProps<{ admin?: boolean }>()
const { act, busy } = useAction()
const status = ref(props.admin ? 'pending' : '')
const page = ref(1)
const list = useAsync(() => paymentsApi.list({ status: status.value || undefined, page: page.value }))
const kind = (s: Order['status']) => (s === 'paid' ? 'success' : s === 'pending' ? 'warning' : s === 'refunded' ? 'info' : 'default')

async function markPaid(o: Order) {
  if (await act(() => paymentsApi.markPaid(o.id), 'Оплата подтверждена')) list.run()
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
              :subtitle="admin ? 'Подтверждайте оплату наличными или переводом — ученик сразу получит доступ.' : undefined" />

  <div class="row" style="margin-bottom: 16px">
    <select v-model="status" style="max-width: 220px" @change="page = 1; list.run()">
      <option value="">Все</option>
      <option v-for="(label, key) in orderStatusLabels" :key="key" :value="key">{{ label }}</option>
    </select>
  </div>

  <StateBlock :loading="list.loading.value" :error="list.error.value" :empty="!list.data.value?.results.length"
              empty-text="Заказов нет." @retry="list.run">
    <div class="card table-wrap">
      <table class="table">
        <thead><tr><th>#</th><th>Курс</th><th v-if="admin">Покупатель</th><th>Сумма</th><th>Способ</th><th>Статус</th><th>Дата</th><th></th></tr></thead>
        <tbody>
          <tr v-for="o in list.data.value?.results ?? []" :key="o.id">
            <td>{{ o.id }}</td>
            <td><RouterLink :to="`/courses/${o.course}`">{{ o.course_title }}</RouterLink></td>
            <td v-if="admin">{{ o.user_email }}</td>
            <td>{{ fmtMoney(o.amount, o.currency) }}</td>
            <td>{{ o.provider }}</td>
            <td><AppBadge :kind="kind(o.status)">{{ orderStatusLabels[o.status] }}</AppBadge></td>
            <td class="small">{{ fmtDateTime(o.paid_at ?? o.created_at) }}</td>
            <td class="row">
              <a v-if="o.status === 'pending' && o.checkout_url" :href="o.checkout_url" class="btn btn--sm">Оплатить</a>
              <template v-if="admin">
                <button v-if="o.status === 'pending'" class="btn btn--success btn--sm" :disabled="busy"
                        @click="markPaid(o)">Подтвердить оплату</button>
                <button v-if="o.status === 'paid'" class="btn btn--ghost btn--sm" :disabled="busy"
                        @click="refund(o)">Возврат</button>
              </template>
              <button v-if="o.status === 'pending'" class="btn btn--ghost btn--sm" :disabled="busy"
                      @click="cancel(o)">Отменить</button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <AppPager :page="page" :total-pages="list.data.value?.total_pages ?? 1" @change="(p) => { page = p; list.run() }" />
  </StateBlock>
</template>
