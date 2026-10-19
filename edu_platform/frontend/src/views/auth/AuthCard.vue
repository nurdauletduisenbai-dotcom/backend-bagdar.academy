<script setup lang="ts">
/** Вход/регистрация: слева teal-панель с брендом, справа форма (вайрфрейм 2a) */
defineProps<{ title: string; subtitle?: string }>()
</script>

<template>
  <div class="auth">
    <aside class="auth__brand">
      <RouterLink to="/" class="auth__logo">bagdar<span>.</span></RouterLink>
      <div class="auth__pitch">
        <div class="eyebrow">bagdar.academy</div>
        <p class="auth__slogan">Учитесь думать, а&nbsp;не просто сдавать.</p>
        <p class="auth__note">Видеоуроки, тесты, домашние задания и расписание — в одном месте для учеников, родителей и учителей.</p>
      </div>
      <div class="auth__langs">RU · KK · EN</div>
    </aside>
    <section class="auth__form">
      <div class="auth__inner">
        <h1>{{ title }}</h1>
        <p v-if="subtitle" class="muted">{{ subtitle }}</p>
        <slot />
      </div>
    </section>
  </div>
</template>

<style scoped>
.auth {
  min-height: 100vh;
  display: grid;
  grid-template-columns: minmax(320px, 5fr) 7fr;
}
.auth__brand {
  background: radial-gradient(120% 80% at 0% 0%, var(--teal-700) 0%, var(--teal-900) 60%);
  color: var(--text-on-dark);
  padding: var(--space-xxxl);
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  gap: var(--space-xxl);
}
.auth__logo {
  font-size: 26px;
  font-weight: 600;
  letter-spacing: -0.5px;
  color: var(--text-on-dark);
  text-decoration: none;
}
.auth__logo span {
  color: var(--green-500);
}
.auth__pitch .eyebrow {
  color: var(--green-500);
}
.auth__pitch {
  display: grid;
  gap: var(--space-md);
  max-width: 460px;
}
.auth__slogan {
  font: 500 var(--fs-h2) / var(--lh-h2) var(--font-sans);
  letter-spacing: -0.5px;
  margin: 0;
}
.auth__note {
  color: var(--text-on-dark-muted);
  margin: 0;
}
.auth__langs {
  font-size: var(--fs-caption);
  color: var(--text-on-dark-muted);
  letter-spacing: 1px;
}
.auth__form {
  display: grid;
  place-items: center;
  padding: var(--space-xxxl) var(--space-xl);
  background: var(--canvas);
}
.auth__inner {
  width: min(420px, 100%);
  display: grid;
  gap: var(--space-md);
}
.auth__inner > p {
  margin: -8px 0 0;
}
@media (max-width: 860px) {
  .auth {
    grid-template-columns: 1fr;
  }
  .auth__brand {
    padding: var(--space-xl);
    gap: var(--space-md);
  }
  .auth__slogan {
    font-size: var(--fs-h4);
  }
  .auth__note,
  .auth__langs {
    display: none;
  }
}
</style>
