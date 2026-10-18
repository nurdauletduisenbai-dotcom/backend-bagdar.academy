<script setup lang="ts">
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { errorMessage } from '@/api/http'
import { useAuthStore } from '@/stores/auth'

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
      const next = typeof route.query.next === 'string' ? route.query.next : '/'
      router.push(next)
    }
  } catch (e) {
    error.value = errorMessage(e)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <section class="card login">
    <h1>Вход</h1>
    <form @submit.prevent="onSubmit">
      <label>
        Email
        <input v-model="email" type="email" autocomplete="email" required />
      </label>
      <label>
        Пароль
        <input v-model="password" type="password" autocomplete="current-password" required />
      </label>
      <label v-if="needs2fa">
        Код из приложения-аутентификатора
        <input v-model="totpCode" inputmode="numeric" autocomplete="one-time-code" required />
      </label>
      <p v-if="error" class="error">{{ error }}</p>
      <button class="btn" type="submit" :disabled="loading">
        {{ loading ? 'Входим…' : 'Войти' }}
      </button>
    </form>
  </section>
</template>

<style scoped>
.login {
  max-width: 400px;
  margin: 48px auto;
}
form {
  display: grid;
  gap: 16px;
}
label {
  display: grid;
  gap: 6px;
  font-size: 14px;
}
</style>
