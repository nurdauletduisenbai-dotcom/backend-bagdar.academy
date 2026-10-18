<script setup lang="ts">
defineProps<{ title: string; wide?: boolean }>()
</script>

<template>
  <div class="auth-page">
    <section class="card auth-card" :class="{ wide }">
      <RouterLink to="/" class="logo">EduPlatform</RouterLink>
      <h1>{{ title }}</h1>
      <slot />
    </section>
  </div>
</template>

<style scoped>
.auth-page {
  min-height: 100vh;
  display: grid;
  place-items: center;
  padding: 24px 16px;
}
.auth-card {
  width: min(420px, 100%);
}
.auth-card.wide {
  width: min(860px, 100%);
}
.logo {
  font-weight: 700;
  color: var(--text);
  text-decoration: none;
}
h1 {
  font-size: 22px;
  margin: 8px 0 16px;
}
</style>
