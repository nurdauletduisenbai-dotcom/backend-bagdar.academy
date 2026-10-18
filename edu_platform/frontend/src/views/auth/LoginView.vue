<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { errorMessage } from '@/api/http'
import { demoAccounts, showDemoAccounts, type DemoAccount } from '@/demo'
import { useAuthStore } from '@/stores/auth'

import AuthCard from './AuthCard.vue'

const auth = useAuthStore()
const router = useRouter()
const route = useRoute()

const email = ref('')
const password = ref('')
const totpCode = ref('')
const needs2fa = ref(false)
const error = ref('')
const loading = ref(false)

async function onSubmit() {
  error.value = ''
  loading.value = true
  try {
    needs2fa.value = await auth.login({
      email: email.value,
      password: password.value,
      totp_code: totpCode.value || undefined,
    })
    if (!needs2fa.value) {
      router.push(typeof route.query.next === 'string' ? route.query.next : '/')
    }
  } catch (e) {
    error.value = errorMessage(e)
  } finally {
    loading.value = false
  }
}

function useDemo(account: DemoAccount) {
  email.value = account.email
  password.value = account.password
  totpCode.value = ''
  needs2fa.value = false
  onSubmit()
}
</script>

<template>
  <AuthCard title="Вход" :wide="showDemoAccounts">
    <div :class="{ 'login-grid': showDemoAccounts }">
      <form class="form" @submit.prevent="onSubmit">
        <label>Email <input v-model="email" type="email" autocomplete="email" required /></label>
        <label>Пароль <input v-model="password" type="password" autocomplete="current-password" required /></label>
        <label v-if="needs2fa">
          Код 2FA (или резервный код)
          <input v-model="totpCode" inputmode="numeric" autocomplete="one-time-code" required autofocus />
        </label>
        <p v-if="error" class="error">{{ error }}</p>
        <button class="btn" type="submit" :disabled="loading">{{ loading ? 'Входим…' : 'Войти' }}</button>
        <div class="row row--between small">
          <RouterLink to="/register">Регистрация</RouterLink>
          <RouterLink to="/forgot-password">Забыли пароль?</RouterLink>
        </div>
        <RouterLink to="/invite" class="small">У меня есть приглашение</RouterLink>
      </form>

      <div v-if="showDemoAccounts">
        <h2>Демо-аккаунты</h2>
        <p class="muted small">Нажмите, чтобы войти под ролью. Данные создаются командой <code>make seed</code>.</p>
        <ul class="list-plain">
          <li v-for="a in demoAccounts" :key="a.email" class="demo" @click="useDemo(a)">
            <div class="row row--between">
              <strong>{{ a.role }}</strong>
              <span class="muted small">{{ a.email }}</span>
            </div>
            <span class="muted small">{{ a.note }}</span>
          </li>
        </ul>
      </div>
    </div>
  </AuthCard>
</template>

<style scoped>
.login-grid {
  display: grid;
  grid-template-columns: 1fr 1.2fr;
  gap: 32px;
  align-items: start;
}
@media (max-width: 760px) {
  .login-grid {
    grid-template-columns: 1fr;
  }
}
.demo {
  cursor: pointer;
}
.demo:hover {
  border-color: var(--primary);
}
</style>
