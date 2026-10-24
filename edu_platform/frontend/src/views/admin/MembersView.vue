<script setup lang="ts">
import { reactive, ref } from 'vue'

import { orgsApi } from '@/api/orgs'
import AppBadge from '@/components/ui/AppBadge.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import AppPager from '@/components/ui/AppPager.vue'
import PageHeader from '@/components/ui/PageHeader.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAction, useAsync } from '@/composables/useAsync'
import { useAuthStore } from '@/stores/auth'
import type { Member, Role } from '@/types/api'
import { fmtDate, roleLabels } from '@/utils/format'

const auth = useAuthStore()
const { act, busy } = useAction()
const filters = reactive({ role: '' as Role | '', search: '', page: 1 })
const members = useAsync(() => orgsApi.members({ role: filters.role || undefined, search: filters.search || undefined, page: filters.page }))
const add = reactive({ email: '', role: 'student' as Role })
const addOpen = ref(false)

function apply() {
  filters.page = 1
  members.run()
}

async function changeRole(m: Member, role: Role) {
  if (await act(() => orgsApi.updateMember(m.id, { role }), 'Роль изменена')) members.run()
}

async function toggleActive(m: Member) {
  const fn = (): Promise<unknown> =>
    m.is_active ? orgsApi.deactivateMember(m.id) : orgsApi.updateMember(m.id, { is_active: true })
  if (await act(fn, m.is_active ? 'Участник отключён' : 'Участник включён')) members.run()
}

async function addMember() {
  if (await act(() => orgsApi.addMember(add.email, add.role), 'Участник добавлен')) {
    add.email = ''
    addOpen.value = false
    members.run()
  }
}
</script>

<template>
  <PageHeader title="Участники">
    <button v-if="auth.isAdmin" class="btn btn--ghost" @click="addOpen = !addOpen">+ Существующий пользователь</button>
    <RouterLink to="/admin/invites" class="btn">+ Пригласить</RouterLink>
  </PageHeader>

  <form v-if="addOpen" class="card row" style="margin-bottom: var(--space-lg)" @submit.prevent="addMember">
    <input v-model="add.email" type="email" placeholder="email зарегистрированного пользователя" style="max-width: 300px" required />
    <select v-model="add.role" style="max-width: 180px">
      <option v-for="(label, key) in roleLabels" :key="key" :value="key">{{ label }}</option>
    </select>
    <button class="btn" :disabled="busy">Добавить</button>
  </form>

  <div class="row row--between" style="margin-bottom: var(--space-lg)">
    <div class="pills">
      <button class="pill" :class="{ active: !filters.role }" @click="filters.role = ''; apply()">Все <span class="count">{{ filters.role ? '' : members.data.value?.total ?? '' }}</span></button>
      <button class="pill" :class="{ active: filters.role === 'student' }" @click="filters.role = 'student'; apply()">Ученики</button>
      <button class="pill" :class="{ active: filters.role === 'teacher' }" @click="filters.role = 'teacher'; apply()">Учителя</button>
      <button class="pill" :class="{ active: filters.role === 'parent' }" @click="filters.role = 'parent'; apply()">Родители</button>
      <button class="pill" :class="{ active: filters.role === 'curator' }" @click="filters.role = 'curator'; apply()">Кураторы</button>
      <button class="pill" :class="{ active: filters.role === 'admin' }" @click="filters.role = 'admin'; apply()">Админы</button>
      <RouterLink v-if="auth.isTeacher" to="/admin/invites" class="pill">Приглашения</RouterLink>
    </div>
    <form class="search" style="width: 260px" @submit.prevent="apply">
      <AppIcon name="search" /><input v-model="filters.search" type="search" placeholder="Имя или email" aria-label="Поиск участников" />
    </form>
  </div>

  <StateBlock :loading="members.loading.value" :error="members.error.value" :empty="!members.data.value?.results.length" @retry="members.run">
    <div class="card card--flush table-wrap">
      <table class="table">
        <thead><tr><th>Пользователь</th><th>Роль</th><th>С</th><th>Статус</th><th></th></tr></thead>
        <tbody>
          <tr v-for="m in members.data.value?.results ?? []" :key="m.id">
            <td><strong>{{ m.full_name }}</strong><div class="muted small">{{ m.email }}</div></td>
            <td>
              <select v-if="auth.isAdmin" :value="m.role" style="max-width: 170px; height: 36px" @change="changeRole(m, ($event.target as HTMLSelectElement).value as Role)">
                <option v-for="(label, key) in roleLabels" :key="key" :value="key">{{ label }}</option>
              </select>
              <span v-else>{{ roleLabels[m.role] }}</span>
            </td>
            <td class="small">{{ fmtDate(m.created_at) }}</td>
            <td><AppBadge :kind="m.is_active ? 'success' : 'default'">{{ m.is_active ? 'Активен' : 'Отключён' }}</AppBadge></td>
            <td>
              <button v-if="auth.isAdmin && m.user !== auth.user?.id" class="btn btn--text btn--sm" :disabled="busy" @click="toggleActive(m)">
                {{ m.is_active ? 'Отключить' : 'Включить' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <AppPager :page="filters.page" :total-pages="members.data.value?.total_pages ?? 1" @change="(p) => { filters.page = p; members.run() }" />
  </StateBlock>
</template>
