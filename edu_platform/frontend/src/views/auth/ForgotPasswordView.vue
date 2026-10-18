<script setup lang="ts">
import { ref } from 'vue'

import { authApi } from '@/api/auth'
import { errorMessage } from '@/api/http'

import AuthCard from './AuthCard.vue'

const email = ref('')
const message = ref('')
const error = ref('')

async function onSubmit() {
  error.value = ''
  try {
    message.value = (await authApi.requestPasswordReset(email.value)).message
  } catch (e) {
    error.value = errorMessage(e)
  }
}
</script>

<template>
  <AuthCard title="Восстановление пароля">
    <div v-if="message" class="stack">
      <div class="alert alert--success">{{ message }}</div>
      <p class="muted small">Локально письмо смотрите в MailHog: <a href="http://localhost:8025" target="_blank">localhost:8025</a></p>
    </div>
    <form v-else class="form" @submit.prevent="onSubmit">
      <label>Email <input v-model="email" type="email" required /></label>
      <p v-if="error" class="error">{{ error }}</p>
      <button class="btn">Отправить ссылку</button>
      <RouterLink to="/login" class="small">← Ко входу</RouterLink>
    </form>
  </AuthCard>
</template>
