<script setup lang="ts">
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const router = useRouter()

async function onLogout() {
  await auth.logout()
  router.push({ name: 'login' })
}
</script>

<template>
  <header class="header">
    <div class="container header__inner">
      <RouterLink to="/" class="header__logo">EduPlatform</RouterLink>
      <div v-if="auth.user" class="header__user">
        <span>{{ auth.user.full_name || auth.user.email }}</span>
        <button class="btn btn--ghost" @click="onLogout">Выйти</button>
      </div>
    </div>
  </header>
</template>

<style scoped>
.header {
  border-bottom: 1px solid var(--border);
  background: var(--surface);
}
.header__inner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  height: 56px;
}
.header__logo {
  font-weight: 700;
  color: var(--text);
  text-decoration: none;
}
.header__user {
  display: flex;
  align-items: center;
  gap: 12px;
}
</style>
