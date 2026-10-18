<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'

import { authApi } from '@/api/auth'
import { errorMessage } from '@/api/http'
import { useAuthStore } from '@/stores/auth'

import AuthCard from './AuthCard.vue'

const route = useRoute()
const auth = useAuthStore()
const state = ref<'loading' | 'ok' | 'error'>('loading')
const error = ref('')

onMounted(async () => {
  try {
    await authApi.verifyEmail(String(route.query.token ?? ''))
    state.value = 'ok'
    if (auth.isAuthenticated) await auth.loadProfile(auth.user?.org_id ?? null)
  } catch (e) {
    error.value = errorMessage(e)
    state.value = 'error'
  }
})
</script>

<template>
  <AuthCard title="Подтверждение email">
    <p v-if="state === 'loading'" class="muted">Проверяем ссылку…</p>
    <div v-else-if="state === 'ok'" class="stack">
      <div class="alert alert--success">Email подтверждён.</div>
      <RouterLink to="/" class="btn">Продолжить</RouterLink>
    </div>
    <div v-else class="alert alert--error">{{ error }}</div>
  </AuthCard>
</template>
