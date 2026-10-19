<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'

import { authApi } from '@/api/auth'
import { errorMessage } from '@/api/http'

import AuthCard from './AuthCard.vue'

const route = useRoute()
const token = typeof route.query.token === 'string' ? route.query.token : ''
const password = ref('')
const done = ref(false)
const error = ref('')

async function onSubmit() {
  error.value = ''
  try {
    await authApi.confirmPasswordReset(token, password.value)
    done.value = true
  } catch (e) {
    error.value = errorMessage(e)
  }
}
</script>

<template>
  <AuthCard title="Новый пароль">
    <div v-if="!token" class="alert alert--error">В ссылке нет токена. Запросите сброс ещё раз.</div>
    <div v-else-if="done" class="stack">
      <div class="alert alert--success">Пароль изменён.</div>
      <RouterLink to="/login" class="btn">Войти</RouterLink>
    </div>
    <form v-else class="form" @submit.prevent="onSubmit">
      <label>Новый пароль (от 10 символов) <input v-model="password" type="password" minlength="10" required /></label>
      <p v-if="error" class="alert alert--error">{{ error }}</p>
      <button class="btn btn--lg btn--block">Сохранить</button>
    </form>
  </AuthCard>
</template>
