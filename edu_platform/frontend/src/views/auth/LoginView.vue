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
  <AuthCard :title="$t('auth.loginTitle')" :subtitle="$t('auth.loginSubtitle')">
    <form class="form" @submit.prevent="onSubmit">
      <label>{{ $t('auth.email') }} <input v-model="email" type="email" autocomplete="email" placeholder="you@school.kz" required /></label>
      <label>{{ $t('auth.password') }} <input v-model="password" type="password" autocomplete="current-password" required /></label>
      <label v-if="needs2fa">
        Код двухфакторной защиты (или резервный код)
        <input v-model="totpCode" inputmode="numeric" autocomplete="one-time-code" placeholder="123 456" required autofocus />
      </label>
      <p v-if="error" class="alert alert--error">{{ error }}</p>
      <button class="btn btn--lg btn--block" type="submit" :disabled="loading">
        {{ loading ? 'Входим…' : needs2fa ? 'Продолжить' : $t('auth.submit') }}
      </button>
      <div class="row row--between small">
        <RouterLink to="/forgot-password">{{ $t('auth.forgotPassword') }}</RouterLink>
        <RouterLink to="/register">{{ $t('auth.register') }}</RouterLink>
      </div>
      <RouterLink to="/invite" class="small">{{ $t('auth.haveInvite') }} →</RouterLink>
    </form>

    <div v-if="showDemoAccounts" class="demo">
      <div class="eyebrow">{{ $t('auth.demoLogin') }}</div>
      <div class="pills">
        <button v-for="a in demoAccounts" :key="a.email" type="button" class="pill" :title="`${a.email} — ${a.note}`"
                :disabled="loading" @click="useDemo(a)">
          {{ a.role }}
        </button>
      </div>
      <p class="muted small">Аккаунты создаются командой <code>make seed</code>. Наведите на кнопку — увидите, что проверить.</p>
    </div>
  </AuthCard>
</template>

<style scoped>
.demo {
  display: grid;
  gap: var(--space-sm);
  padding-top: var(--space-lg);
  margin-top: var(--space-xs);
  border-top: 1px dashed var(--border-strong);
}
.demo p {
  margin: 0;
}
</style>
