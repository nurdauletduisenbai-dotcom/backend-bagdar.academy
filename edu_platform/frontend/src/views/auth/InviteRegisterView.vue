<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute } from 'vue-router'

import { authApi } from '@/api/auth'
import { errorMessage } from '@/api/http'

import AuthCard from './AuthCard.vue'

const route = useRoute()
const form = reactive({
  invite_token: typeof route.query.token === 'string' ? route.query.token : '',
  email: '', password: '', first_name: '', last_name: '',
})
const error = ref('')
const done = ref(false)

async function onSubmit() {
  error.value = ''
  try {
    await authApi.registerByInvite(form)
    done.value = true
  } catch (e) {
    error.value = errorMessage(e)
  }
}
</script>

<template>
  <AuthCard title="Регистрация по приглашению">
    <div v-if="done" class="stack">
      <div class="alert alert--success">Аккаунт создан.</div>
      <RouterLink to="/login" class="btn">Войти</RouterLink>
    </div>
    <form v-else class="form" @submit.prevent="onSubmit">
      <label>Код приглашения <input v-model="form.invite_token" required /></label>
      <div class="form-row">
        <label>Имя <input v-model="form.first_name" required /></label>
        <label>Фамилия <input v-model="form.last_name" required /></label>
      </div>
      <label>Email <input v-model="form.email" type="email" required /></label>
      <label>Пароль (от 10 символов) <input v-model="form.password" type="password" minlength="10" required /></label>
      <p v-if="error" class="error">{{ error }}</p>
      <button class="btn">Создать аккаунт</button>
    </form>
  </AuthCard>
</template>
