<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import AppIcon from '@/components/ui/AppIcon.vue'
import LangSwitcher from '@/components/ui/LangSwitcher.vue'
import { useAuthStore } from '@/stores/auth'

/** Публичные страницы (главная, новости): шапка с «Войти»/«Регистрация» и подвал */
const auth = useAuthStore()
const route = useRoute()
const menuOpen = ref(false)

const links = [
  { to: { path: '/', hash: '#about' }, key: 'public.about' },
  { to: { path: '/', hash: '#courses' }, key: 'public.courses' },
  { to: { path: '/news' }, key: 'public.news' },
  { to: { path: '/', hash: '#start' }, key: 'public.howItWorks' },
]

watch(() => route.fullPath, () => (menuOpen.value = false))
</script>

<template>
  <header class="pub-nav">
    <div class="pub-nav__inner">
      <RouterLink to="/" class="brand">bagdar<span class="brand__dot">.</span></RouterLink>

      <nav class="pub-nav__links" :class="{ open: menuOpen }">
        <RouterLink v-for="l in links" :key="l.key" :to="l.to" class="pub-nav__link"
                    :class="{ active: l.to.path === '/news' && route.path.startsWith('/news') }">
          {{ $t(l.key) }}
        </RouterLink>
        <div class="pub-nav__menu-lang"><LangSwitcher /></div>
      </nav>

      <div class="pub-nav__right">
        <LangSwitcher />
        <template v-if="auth.isAuthenticated">
          <RouterLink to="/home" class="btn btn--sm">{{ $t('public.cabinet') }}</RouterLink>
        </template>
        <template v-else>
          <RouterLink to="/login" class="btn btn--ghost btn--sm">{{ $t('public.login') }}</RouterLink>
          <RouterLink to="/register" class="btn btn--sm">{{ $t('public.register') }}</RouterLink>
        </template>
        <button class="icon-btn burger" :aria-label="$t('public.menu')" :aria-expanded="menuOpen" @click="menuOpen = !menuOpen">
          <AppIcon name="menu" />
        </button>
      </div>
    </div>
  </header>

  <main>
    <RouterView :key="route.path" />
  </main>

  <footer class="pub-footer">
    <div class="container pub-footer__inner">
      <div class="pub-footer__brand">
        <RouterLink to="/" class="brand brand--dark">bagdar<span class="brand__dot">.</span></RouterLink>
        <p class="pub-footer__note">{{ $t('public.footerNote') }}</p>
      </div>
      <nav class="pub-footer__links">
        <RouterLink v-for="l in links" :key="l.key" :to="l.to">{{ $t(l.key) }}</RouterLink>
      </nav>
      <nav class="pub-footer__links">
        <RouterLink to="/login">{{ $t('public.login') }}</RouterLink>
        <RouterLink to="/register">{{ $t('public.register') }}</RouterLink>
        <RouterLink to="/invite">{{ $t('auth.haveInvite') }}</RouterLink>
      </nav>
    </div>
    <div class="container pub-footer__bottom">
      <span>© 2026 bagdar.academy · {{ $t('public.rights') }}</span>
      <LangSwitcher dark />
    </div>
  </footer>
</template>

<style scoped>
.pub-nav {
  position: sticky;
  top: 0;
  z-index: 30;
  background: var(--canvas);
  border-bottom: 1px solid var(--border-default);
}
.pub-nav__inner {
  max-width: var(--container-max);
  margin: 0 auto;
  padding: 0 var(--gutter);
  height: var(--nav-height);
  display: flex;
  align-items: center;
  gap: var(--space-xxl);
}
.brand {
  font-size: 22px;
  font-weight: 600;
  letter-spacing: -0.5px;
  color: var(--text-strong);
  text-decoration: none;
}
.brand--dark {
  color: var(--text-on-dark);
}
.brand__dot {
  color: var(--green-600);
}
.brand--dark .brand__dot {
  color: var(--green-500);
}
.pub-nav__links {
  display: flex;
  gap: 4px;
  flex: 1;
  min-width: 0;
}
.pub-nav__link {
  padding: 8px 12px;
  border-radius: var(--radius-md);
  font: 500 var(--fs-body-sm) / var(--lh-body-sm) var(--font-sans);
  color: var(--text-secondary);
  text-decoration: none;
  white-space: nowrap;
}
.pub-nav__link:hover,
.pub-nav__link.active {
  color: var(--text-strong);
  background: var(--surface-subtle);
  text-decoration: none;
}
.pub-nav__right {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}
.burger {
  display: none;
}
.pub-nav__menu-lang {
  display: none;
}

.pub-footer {
  background: var(--surface-dark);
  color: var(--text-on-dark-muted);
  margin-top: var(--space-section);
  padding: var(--space-section-sm) 0 var(--space-xl);
}
.pub-footer__inner {
  display: grid;
  grid-template-columns: 2fr 1fr 1fr;
  gap: var(--space-xxl);
}
.pub-footer__note {
  max-width: 360px;
  margin: var(--space-sm) 0 0;
  font-size: var(--fs-body-sm);
}
.pub-footer__links {
  display: grid;
  gap: var(--space-xs);
  align-content: start;
}
.pub-footer__links a {
  color: var(--text-on-dark-muted);
  font-size: var(--fs-body-sm);
  text-decoration: none;
}
.pub-footer__links a:hover {
  color: var(--text-on-dark);
}
.pub-footer__bottom {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: var(--space-md);
  margin-top: var(--space-xxl);
  padding-top: var(--space-lg);
  border-top: 1px solid var(--border-dark);
  font-size: var(--fs-caption);
}

@media (max-width: 960px) {
  .pub-nav__inner {
    gap: var(--space-sm);
    padding: 0 var(--space-md);
  }
  .brand {
    flex: 1;
  }
  .burger {
    display: inline-grid;
  }
  .pub-nav__links {
    display: none;
  }
  .pub-nav__links.open {
    display: grid;
    position: absolute;
    top: var(--nav-height);
    left: 0;
    right: 0;
    padding: var(--space-xs) var(--space-md) var(--space-md);
    background: var(--canvas);
    border-bottom: 1px solid var(--border-default);
    box-shadow: var(--shadow-2);
  }
}
@media (max-width: 640px) {
  .pub-nav__right > :deep(.lang-switcher) {
    display: none;
  }
  .pub-nav__menu-lang {
    display: block;
    padding: var(--space-xs) 12px 0;
  }
  .pub-footer__inner {
    grid-template-columns: 1fr;
  }
  .pub-footer__bottom {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
