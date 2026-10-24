<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AppIcon from '@/components/ui/AppIcon.vue'
import LangSwitcher from '@/components/ui/LangSwitcher.vue'
import { useAuthStore } from '@/stores/auth'
import { useLocaleStore } from '@/stores/locale'
import { useNotificationsStore } from '@/stores/notifications'
import { useToast } from '@/stores/toast'
import { roleLabel } from '@/utils/format'

import { menuLinks, topLinks } from './navigation'

const auth = useAuthStore()
const notifications = useNotificationsStore()
const toast = useToast()
const router = useRouter()
const route = useRoute()
const locale = useLocaleStore()

const menuOpen = ref(false)
const mobileOpen = ref(false)
const menuRef = ref<HTMLElement | null>(null)

const top = computed(() => topLinks(auth.roles))
const more = computed(() => menuLinks(auth.roles))
const initials = computed(() =>
  (auth.user?.full_name || auth.user?.email || '?')
    .split(' ')
    .map((p) => p[0])
    .slice(0, 2)
    .join('')
    .toUpperCase(),
)
const roleText = computed(() => auth.roles.map((r) => roleLabel(r)).join(', ') || '—')

/** Активен самый «длинный» подходящий пункт: на /admin/orders горит «Оплаты», а не «Сводка» (/admin) */
const activeTo = computed(() => {
  const all = [...top.value, ...more.value].map((i) => i.to)
  const matches = all.filter((to) => (route.path === to || route.path.startsWith(`${to}/`)))
  return matches.sort((a, b) => b.length - a.length)[0] ?? null
})

function isActive(to: string) {
  return activeTo.value === to
}

async function onOrgChange(event: Event) {
  const orgId = Number((event.target as HTMLSelectElement).value)
  await auth.switchOrg(orgId)
  toast.info(`Организация: ${auth.currentOrg?.name}`)
  menuOpen.value = false
  router.push('/home')
}

async function onLogout() {
  await auth.logout()
  router.push({ name: 'login' })
}

function onDocClick(e: MouseEvent) {
  if (menuOpen.value && menuRef.value && !menuRef.value.contains(e.target as Node)) menuOpen.value = false
}

watch(() => route.fullPath, () => {
  menuOpen.value = false
  mobileOpen.value = false
})
onMounted(() => {
  notifications.start()
  document.addEventListener('click', onDocClick)
})
onUnmounted(() => {
  notifications.stop()
  document.removeEventListener('click', onDocClick)
})
</script>

<template>
  <header class="topnav">
    <div class="topnav__inner">
      <button class="icon-btn burger" aria-label="Меню" @click="mobileOpen = !mobileOpen"><AppIcon name="menu" /></button>
      <RouterLink to="/home" class="brand">bagdar<span class="brand__dot">.</span></RouterLink>

      <nav class="topnav__links" :class="{ open: mobileOpen }">
        <RouterLink v-for="item in top" :key="item.to" :to="item.to" class="topnav__link" :class="{ active: isActive(item.to) }">
          {{ $t(item.labelKey) }}
        </RouterLink>
        <!-- На телефоне в выпадающем меню показываем сразу все разделы -->
        <template v-if="mobileOpen">
          <RouterLink v-for="item in more" :key="item.to" :to="item.to" class="topnav__link topnav__link--extra"
                      :class="{ active: isActive(item.to) }">
            {{ $t(item.labelKey) }}
          </RouterLink>
        </template>
      </nav>

      <div class="topnav__right">
        <LangSwitcher class="lang-switcher--nav" />
        <RouterLink to="/notifications" class="icon-btn" :title="$t('nav.notifications')" :aria-label="$t('nav.notifications')">
          <AppIcon name="bell" />
          <span v-if="notifications.unread" class="bell-count">{{ notifications.unread > 99 ? '99+' : notifications.unread }}</span>
        </RouterLink>

        <div ref="menuRef" class="user-menu">
          <button class="avatar" :aria-expanded="menuOpen" aria-label="Меню пользователя" @click="menuOpen = !menuOpen">
            {{ initials }}
          </button>
          <div v-if="menuOpen" class="dropdown">
            <div class="dropdown__head">
              <strong>{{ auth.user?.full_name || auth.user?.email }}</strong>
              <span class="muted small">{{ auth.user?.email }} · {{ roleText }}</span>
            </div>
            <label v-if="auth.organizations.length > 1" class="dropdown__org">
              <span class="eyebrow">{{ $t('organization') }}</span>
              <select :value="auth.user?.org_id ?? ''" @change="onOrgChange">
                <option v-for="org in auth.organizations" :key="org.id" :value="org.id">{{ org.name }}</option>
              </select>
            </label>
            <div v-else-if="auth.currentOrg" class="dropdown__org">
              <span class="eyebrow">{{ $t('organization') }}</span>
              <span class="small">{{ auth.currentOrg.name }}</span>
            </div>
            <nav class="dropdown__links">
              <RouterLink to="/profile">{{ $t('nav.profile') }}</RouterLink>
              <RouterLink v-for="item in more" :key="item.to" :to="item.to">{{ $t(item.labelKey) }}</RouterLink>
            </nav>
            <button class="dropdown__logout" @click="onLogout"><AppIcon name="logout" :size="16" /> {{ $t('logout') }}</button>
          </div>
        </div>
      </div>
    </div>
  </header>

  <div v-if="auth.user && !auth.user.is_verified" class="verify-bar">
    <div class="container row row--between">
      <span>Email не подтверждён. Письмо со ссылкой — в почте (локально: MailHog, localhost:8025).</span>
      <RouterLink to="/profile" class="btn btn--sm btn--dark">Отправить ещё раз</RouterLink>
    </div>
  </div>

  <main class="container content">
    <!-- key: при переходе /courses/1 → /courses/2 страница пересоздаётся и заново грузит данные -->
    <RouterView :key="route.path" />
  </main>
</template>

<style scoped>
.topnav {
  position: sticky;
  top: 0;
  z-index: 30;
  background: var(--canvas);
  border-bottom: 1px solid var(--border-default);
}
.topnav__inner {
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
.brand__dot {
  color: var(--green-600);
}
.topnav__links {
  display: flex;
  gap: 4px;
  flex: 1;
  min-width: 0;
}
.topnav__link {
  position: relative;
  padding: 8px 12px;
  border-radius: var(--radius-md);
  font: 500 var(--fs-body-sm) / var(--lh-body-sm) var(--font-sans);
  color: var(--text-secondary);
  text-decoration: none;
  white-space: nowrap;
}
.topnav__link:hover {
  color: var(--text-strong);
  background: var(--surface-subtle);
  text-decoration: none;
}
.topnav__link.active {
  color: var(--text-strong);
}
.topnav__link.active::after {
  content: '';
  position: absolute;
  left: 12px;
  right: 12px;
  bottom: -13px;
  height: 2px;
  border-radius: 2px;
  background: var(--green-500);
}
.topnav__link--extra {
  display: none;
}
.topnav__right {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
}
.bell-count {
  position: absolute;
  top: -4px;
  right: -4px;
  min-width: 18px;
  height: 18px;
  padding: 0 5px;
  border-radius: var(--radius-full);
  background: var(--green-500);
  color: var(--teal-900);
  font: 600 11px/18px var(--font-sans);
  text-align: center;
}
.user-menu {
  position: relative;
}
.avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  border: 0;
  background: var(--teal-900);
  color: var(--green-500);
  font: 600 var(--fs-caption) / 1 var(--font-sans);
  cursor: pointer;
}
.dropdown {
  position: absolute;
  right: 0;
  top: calc(100% + 8px);
  width: 290px;
  background: var(--surface-card);
  border: 1px solid var(--border-default);
  border-radius: var(--radius-lg);
  box-shadow: var(--shadow-3);
  overflow: hidden;
}
.dropdown__head {
  display: grid;
  gap: 2px;
  padding: var(--space-md);
  border-bottom: 1px solid var(--border-default);
}
.dropdown__org {
  display: grid;
  gap: 6px;
  padding: var(--space-sm) var(--space-md);
  border-bottom: 1px solid var(--border-default);
}
.dropdown__links {
  display: grid;
  padding: var(--space-xs);
  max-height: 50vh;
  overflow-y: auto;
}
.dropdown__links a {
  padding: 8px 10px;
  border-radius: var(--radius-md);
  color: var(--text-secondary);
  font-size: var(--fs-body-sm);
  text-decoration: none;
}
.dropdown__links a:hover,
.dropdown__links a.router-link-active {
  background: var(--surface-soft);
  color: var(--text-strong);
}
.dropdown__logout {
  display: flex;
  align-items: center;
  gap: var(--space-xs);
  width: 100%;
  padding: var(--space-sm) var(--space-md);
  border: 0;
  border-top: 1px solid var(--border-default);
  background: none;
  font: 500 var(--fs-body-sm) / 1 var(--font-sans);
  color: var(--error-text);
  cursor: pointer;
}
.verify-bar {
  background: var(--warning-bg);
  color: var(--warning-text);
  font-size: var(--fs-body-sm);
  padding: var(--space-xs) 0;
}
.content {
  padding-top: var(--space-xxl);
  padding-bottom: var(--space-section);
}
.burger {
  display: none;
}
@media (max-width: 900px) {
  .topnav__inner {
    gap: var(--space-sm);
    padding: 0 var(--space-md);
  }
  .burger {
    display: inline-grid;
  }
  .brand {
    flex: 1;
  }
  .topnav__links {
    display: none;
  }
  .topnav__links.open {
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
  .topnav__link--extra {
    display: block;
  }
  .topnav__link.active::after {
    display: none;
  }
  .topnav__link.active {
    background: var(--surface-soft);
  }
}
@media (max-width: 640px) {
  .container {
    padding: 0 var(--space-md);
  }
  .content {
    padding-top: var(--space-xl);
  }
}
</style>
