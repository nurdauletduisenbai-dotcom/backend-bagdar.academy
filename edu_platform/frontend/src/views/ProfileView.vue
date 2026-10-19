<script setup lang="ts">
import QRCode from 'qrcode'
import { onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { authApi, parentsApi } from '@/api/auth'
import { notificationsApi } from '@/api/notifications'
import PageHeader from '@/components/ui/PageHeader.vue'
import StateBlock from '@/components/ui/StateBlock.vue'
import { useAction, useAsync } from '@/composables/useAsync'
import { useAuthStore } from '@/stores/auth'
import type { TwoFactorSetup } from '@/types/api'
import { fmtDateTime } from '@/utils/format'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()
const { act, busy } = useAction()
const tab = ref<'profile' | 'security' | 'notifications' | 'parents'>('profile')

// ---------- Профиль ----------
const profile = useAsync(() => authApi.me())
const form = reactive({ first_name: '', last_name: '', phone: '', language: 'ru' as 'ru' | 'kk' | 'en', birth_date: '' })
onMounted(async () => {
  const p = await profile.run()
  if (p) Object.assign(form, { first_name: p.first_name, last_name: p.last_name, phone: p.phone ?? '', language: p.language, birth_date: p.birth_date ?? '' })
})

async function saveProfile() {
  await act(() => authApi.updateMe({ ...form, phone: form.phone || null, birth_date: form.birth_date || null }), 'Профиль сохранён')
  await auth.loadProfile(auth.user?.org_id ?? null)
}

// ---------- Безопасность ----------
const passwords = reactive({ old: '', next: '' })
async function changePassword() {
  const ok = await act(() => authApi.changePassword(passwords.old, passwords.next), 'Пароль изменён, войдите заново')
  if (ok) {
    await auth.logout()
    router.push({ name: 'login' })
  }
}

const sessions = useAsync(() => authApi.sessions(), { immediate: false })
async function revoke(id: number) {
  await act(() => authApi.revokeSession(id), 'Сессия завершена')
  sessions.run()
}
async function logoutAll() {
  await act(() => authApi.logoutAll(), 'Выход со всех устройств')
  await auth.logout()
  router.push({ name: 'login' })
}

const twoFa = ref<TwoFactorSetup | null>(null)
const qr = ref('')
const code = ref('')
const backupCodes = ref<string[]>([])
const disableForm = reactive({ password: '', code: '' })
async function startTwoFa() {
  const setup = await act(() => authApi.twoFactorSetup())
  if (setup) {
    twoFa.value = setup
    qr.value = await QRCode.toDataURL(setup.otpauth_uri, { width: 200 })
  }
}
async function enableTwoFa() {
  const result = await act(() => authApi.twoFactorEnable(code.value), '2FA включена')
  if (result) {
    backupCodes.value = result.backup_codes
    twoFa.value = null
  }
}
async function disableTwoFa() {
  await act(() => authApi.twoFactorDisable(disableForm.password, disableForm.code), '2FA отключена')
}

// ---------- Уведомления ----------
const prefs = useAsync(() => notificationsApi.preferences(), { immediate: false })
async function savePrefs() {
  if (prefs.data.value) await act(() => notificationsApi.updatePreferences(prefs.data.value!), 'Настройки сохранены')
}

// ---------- Родители ----------
const requests = useAsync(() => parentsApi.requests(), { immediate: false })
async function confirmParent(id: number) {
  await act(() => parentsApi.confirm(id), 'Доступ родителю открыт')
  requests.run()
}
async function rejectParent(id: number) {
  await act(() => parentsApi.reject(id), 'Доступ закрыт')
  requests.run()
}

function open(next: typeof tab.value) {
  tab.value = next
  if (next === 'security') sessions.run()
  if (next === 'notifications') prefs.run()
  if (next === 'parents') requests.run()
}

onMounted(() => {
  const wanted = route.query.tab
  if (wanted === 'security' || wanted === 'notifications' || wanted === 'parents') open(wanted)
})

async function resend() {
  await act(() => authApi.resendVerification(), 'Письмо отправлено (MailHog: localhost:8025)')
}
</script>

<template>
  <PageHeader title="Профиль и безопасность" :subtitle="auth.user?.email" />

  <div class="split split--nav">
    <nav class="side-nav card">
      <button :class="{ active: tab === 'profile' }" @click="open('profile')">Профиль</button>
      <button :class="{ active: tab === 'security' }" @click="open('security')">Безопасность</button>
      <button :class="{ active: tab === 'notifications' }" @click="open('notifications')">Уведомления</button>
      <button v-if="auth.isStudent" :class="{ active: tab === 'parents' }" @click="open('parents')">Родители</button>
      <RouterLink v-if="auth.hasRole('student', 'parent')" to="/orders">Мои заказы</RouterLink>
    </nav>

    <div class="stack">
      <section v-if="tab === 'profile'" class="card">
        <StateBlock :loading="profile.loading.value" :error="profile.error.value" @retry="profile.run">
          <form class="form" @submit.prevent="saveProfile">
            <div class="form-row">
              <label>Имя <input v-model="form.first_name" required /></label>
              <label>Фамилия <input v-model="form.last_name" required /></label>
            </div>
            <div class="form-row">
              <label>Телефон <input v-model="form.phone" placeholder="+7 …" /></label>
              <label>Дата рождения <input v-model="form.birth_date" type="date" /></label>
              <label>
                Язык
                <select v-model="form.language">
                  <option value="ru">Русский</option>
                  <option value="kk">Қазақша</option>
                  <option value="en">English</option>
                </select>
              </label>
            </div>
            <div class="row">
              <button class="btn" :disabled="busy">Сохранить</button>
              <button v-if="profile.data.value && !profile.data.value.is_verified" type="button" class="btn btn--ghost" @click="resend">
                Подтвердить email
              </button>
            </div>
          </form>
        </StateBlock>
      </section>

      <template v-if="tab === 'security'">
        <section class="card setting">
          <div class="setting__head">
            <div>
              <h2>Двухфакторная защита</h2>
              <p class="muted small">Код из приложения-аутентификатора при каждом входе.</p>
            </div>
            <button v-if="!twoFa && !backupCodes.length" class="btn btn--sm" :disabled="busy" @click="startTwoFa">Настроить</button>
          </div>
          <div v-if="backupCodes.length" class="stack">
            <div class="alert alert--success">2FA включена. Сохраните резервные коды — каждый работает один раз.</div>
            <pre class="code">{{ backupCodes.join('\n') }}</pre>
          </div>
          <div v-else-if="twoFa" class="twofa">
            <img :src="qr" alt="QR-код 2FA" width="180" height="180" />
            <div class="stack">
              <p class="small">Отсканируйте QR-код в Google Authenticator / 1Password и введите код.</p>
              <p class="muted small">Ключ вручную: <code>{{ twoFa.secret }}</code></p>
              <form class="row" @submit.prevent="enableTwoFa">
                <input v-model="code" inputmode="numeric" placeholder="123456" style="max-width: 160px" required />
                <button class="btn" :disabled="busy">Включить</button>
              </form>
            </div>
          </div>
          <details v-else>
            <summary class="small">2FA уже включена? Отключить</summary>
            <form class="form" style="margin-top: var(--space-sm)" @submit.prevent="disableTwoFa">
              <div class="form-row">
                <label>Пароль <input v-model="disableForm.password" type="password" required /></label>
                <label>Код 2FA <input v-model="disableForm.code" required /></label>
              </div>
              <button class="btn btn--danger btn--sm" :disabled="busy" style="justify-self: start">Отключить 2FA</button>
            </form>
          </details>
        </section>

        <section class="card setting">
          <div class="setting__head">
            <h2>Активные сессии</h2>
            <button class="btn btn--danger btn--sm" @click="logoutAll">Выйти на всех устройствах</button>
          </div>
          <StateBlock :loading="sessions.loading.value" :error="sessions.error.value" :empty="!sessions.data.value?.length" @retry="sessions.run">
            <ul class="list-lines">
              <li v-for="s in sessions.data.value ?? []" :key="s.id" class="row row--between">
                <span class="session-info">
                  <span class="small">{{ s.device_info || 'Неизвестное устройство' }}</span>
                  <span class="muted small">{{ s.ip }} · {{ fmtDateTime(s.created_at) }}</span>
                </span>
                <span v-if="s.is_current" class="badge badge--success">это вы</span>
                <button v-else class="btn btn--text btn--sm" @click="revoke(s.id)">Завершить</button>
              </li>
            </ul>
          </StateBlock>
        </section>

        <section class="card setting">
          <h2>Пароль</h2>
          <form class="form" @submit.prevent="changePassword">
            <div class="form-row">
              <label>Текущий пароль <input v-model="passwords.old" type="password" required /></label>
              <label>Новый пароль <input v-model="passwords.next" type="password" minlength="10" required /></label>
            </div>
            <button class="btn btn--ghost" :disabled="busy" style="justify-self: start">Сменить</button>
          </form>
        </section>
      </template>

      <section v-if="tab === 'notifications'" class="card">
        <StateBlock :loading="prefs.loading.value" :error="prefs.error.value" @retry="prefs.run">
          <form v-if="prefs.data.value" class="form" @submit.prevent="savePrefs">
            <label class="inline"><input v-model="prefs.data.value.in_app_enabled" type="checkbox" /> Уведомления в приложении</label>
            <label class="inline"><input v-model="prefs.data.value.email_enabled" type="checkbox" /> Письма на email</label>
            <button class="btn" :disabled="busy" style="justify-self: start">Сохранить</button>
          </form>
        </StateBlock>
      </section>

      <section v-if="tab === 'parents'" class="card">
        <h2>Кто видит мой прогресс</h2>
        <StateBlock :loading="requests.loading.value" :error="requests.error.value" :empty="!requests.data.value?.length"
                    empty-text="Запросов от родителей нет." @retry="requests.run">
          <ul class="list-lines">
            <li v-for="r in requests.data.value ?? []" :key="r.id" class="row row--between">
              <span>{{ r.parent.full_name }} <span class="muted small">{{ r.parent.email }}</span></span>
              <span class="row">
                <span v-if="r.is_confirmed" class="badge badge--success">Подтверждён</span>
                <button v-else class="btn btn--sm" @click="confirmParent(r.id)">Подтвердить</button>
                <button class="btn btn--text btn--sm" @click="rejectParent(r.id)">{{ r.is_confirmed ? 'Закрыть доступ' : 'Отклонить' }}</button>
              </span>
            </li>
          </ul>
        </StateBlock>
      </section>
    </div>
  </div>
</template>

<style scoped>
.side-nav.card {
  padding: var(--space-xs);
  position: sticky;
  top: calc(var(--nav-height) + var(--space-md));
}
.setting {
  display: grid;
  gap: var(--space-md);
}
.setting__head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: var(--space-md);
}
.setting__head h2,
.setting__head p {
  margin: 0;
}
.twofa {
  display: flex;
  gap: var(--space-xl);
  align-items: flex-start;
  flex-wrap: wrap;
}
.twofa p {
  margin: 0;
}
.session-info {
  display: grid;
}
</style>
