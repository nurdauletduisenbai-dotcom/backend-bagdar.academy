<script setup lang="ts">
import { reactive, ref } from 'vue'

import { errorMessage } from '@/api/http'
import { newsApi, type ContactRequestPayload } from '@/api/news'
import { useLocaleStore } from '@/stores/locale'

/** «Остались вопросы?» — заявка менеджеру (POST /news/contact/, видна в Django admin → «Заявки с сайта») */
const locale = useLocaleStore()
const form = reactive<ContactRequestPayload>({
  name: '', phone: '', audience: 'student', message: '', language: '', consent: false,
})
const sending = ref(false)
const done = ref(false)
const error = ref('')

async function onSubmit() {
  error.value = ''
  sending.value = true
  try {
    await newsApi.contact({ ...form, language: locale.current })
    done.value = true
  } catch (e) {
    error.value = errorMessage(e)
  } finally {
    sending.value = false
  }
}
</script>

<template>
  <div v-if="done" class="alert alert--success contact-done" role="status">{{ $t('landing.contactDone') }}</div>
  <form v-else class="form contact-form" @submit.prevent="onSubmit">
    <div class="form-row">
      <label>{{ $t('landing.contactName') }} <input v-model="form.name" autocomplete="name" required maxlength="120" /></label>
      <label>{{ $t('landing.contactPhone') }}
        <input v-model="form.phone" type="tel" autocomplete="tel" inputmode="tel" placeholder="+7 700 000 00 00" required maxlength="32" />
      </label>
    </div>
    <label>{{ $t('landing.contactAudience') }}
      <select v-model="form.audience">
        <option value="student">{{ $t('landing.contactAudStudent') }}</option>
        <option value="parent">{{ $t('landing.contactAudParent') }}</option>
        <option value="school">{{ $t('landing.contactAudSchool') }}</option>
      </select>
    </label>
    <label>{{ $t('landing.contactMessage') }} <textarea v-model="form.message" rows="3" maxlength="2000" /></label>
    <label class="inline consent"><input v-model="form.consent" type="checkbox" required /> {{ $t('landing.contactConsent') }}</label>
    <p v-if="error" class="alert alert--error">{{ error }}</p>
    <button class="btn btn--lg" type="submit" :disabled="sending">
      {{ sending ? $t('landing.contactSending') : $t('landing.contactSubmit') }}
    </button>
  </form>
</template>

<style scoped>
.contact-form {
  gap: var(--space-md);
}
.contact-form .btn {
  justify-self: start;
}
.consent {
  font-size: var(--fs-body-sm);
  color: var(--text-secondary);
}
.contact-done {
  margin: 0;
}
</style>
