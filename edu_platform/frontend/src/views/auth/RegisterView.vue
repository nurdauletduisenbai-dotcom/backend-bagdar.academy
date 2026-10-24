<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRoute } from 'vue-router'

import { authApi } from '@/api/auth'
import { errorMessage } from '@/api/http'

import AuthCard from './AuthCard.vue'

// ?role=parent — с выбора роли на главной странице
const presetRole = useRoute().query.role === 'parent' ? 'parent' : 'student'
const form = reactive({
  email: '', password: '', first_name: '', last_name: '',
  role: presetRole as 'student' | 'parent', org_slug: 'fizmat-school', is_minor: false, parent_consent: false,
})
const error = ref('')
const done = ref('')
const loading = ref(false)

async function onSubmit() {
  error.value = ''
  loading.value = true
  try {
    done.value = (await authApi.register(form)).message
  } catch (e) {
    error.value = errorMessage(e)
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthCard title="Регистрация">
    <div v-if="done" class="stack">
      <div class="alert alert--success">{{ done }}</div>
      <p class="muted small">Локально письма приходят в MailHog: <a href="http://localhost:8025" target="_blank">localhost:8025</a></p>
      <RouterLink to="/login" class="btn">Войти</RouterLink>
    </div>
    <form v-else class="form" @submit.prevent="onSubmit">
      <div class="form-row">
        <label>Имя <input v-model="form.first_name" required /></label>
        <label>Фамилия <input v-model="form.last_name" required /></label>
      </div>
      <label>Email <input v-model="form.email" type="email" required /></label>
      <label>Пароль (от 10 символов) <input v-model="form.password" type="password" minlength="10" required /></label>
      <label>
        Я регистрируюсь как
        <select v-model="form.role">
          <option value="student">Ученик</option>
          <option value="parent">Родитель</option>
        </select>
      </label>
      <label>Код школы (slug) <input v-model="form.org_slug" required /></label>
      <label class="inline"><input v-model="form.is_minor" type="checkbox" /> Мне меньше 14 лет</label>
      <label v-if="form.is_minor" class="inline"><input v-model="form.parent_consent" type="checkbox" /> Родитель согласен</label>
      <p v-if="error" class="alert alert--error">{{ error }}</p>
      <button class="btn btn--lg btn--block" :disabled="loading">Зарегистрироваться</button>
      <p class="small muted">Учителя и кураторы регистрируются по приглашению. <RouterLink to="/login">Уже есть аккаунт</RouterLink></p>
    </form>
  </AuthCard>
</template>
