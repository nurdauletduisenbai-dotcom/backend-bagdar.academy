<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'
import { useNotificationsStore } from '@/stores/notifications'
import { useToast } from '@/stores/toast'
import { roleLabels } from '@/utils/format'

import { navigation } from './navigation'

const auth = useAuthStore()
const notifications = useNotificationsStore()
const toast = useToast()
const router = useRouter()
const route = useRoute()
const menuOpen = ref(false)

const groups = computed(() =>
  navigation
    .map((g) => ({ ...g, items: g.items.filter((i) => !i.roles || auth.hasRole(...i.roles)) }))
    .filter((g) => g.items.length),
)

const roleText = computed(() => auth.roles.map((r) => roleLabels[r]).join(', ') || 'без роли')

async function onOrgChange(event: Event) {
  const orgId = Number((event.target as HTMLSelectElement).value)
  await auth.switchOrg(orgId)
  toast.info(`Организация: ${auth.currentOrg?.name}`)
  router.push('/')
}

async function onLogout() {
  await auth.logout()
  router.push({ name: 'login' })
}

watch(() => route.fullPath, () => (menuOpen.value = false))
onMounted(() => notifications.start())
onUnmounted(() => notifications.stop())
</script>

<template>
  <div class="layout">
    <aside class="sidebar" :class="{ open: menuOpen }">
      <RouterLink to="/" class="sidebar__logo">EduPlatform</RouterLink>
      <nav>
        <div v-for="group in groups" :key="group.title" class="sidebar__group">
          <div class="sidebar__title">{{ group.title }}</div>
          <RouterLink v-for="item in group.items" :key="item.to" :to="item.to" class="sidebar__link"
                      :class="{ active: item.to === '/' ? route.path === '/' : route.path.startsWith(item.to) }">
            {{ item.label }}
            <span v-if="item.to === '/notifications' && notifications.unread" class="count">{{ notifications.unread }}</span>
          </RouterLink>
        </div>
      </nav>
    </aside>

    <div class="main">
      <header class="topbar">
        <button class="btn btn--ghost btn--sm burger" aria-label="Меню" @click="menuOpen = !menuOpen">☰</button>
        <div class="row">
          <select v-if="auth.organizations.length > 1" :value="auth.user?.org_id ?? ''" class="org-select"
                  aria-label="Организация" @change="onOrgChange">
            <option v-for="org in auth.organizations" :key="org.id" :value="org.id">{{ org.name }}</option>
          </select>
          <span v-else-if="auth.currentOrg" class="muted small">{{ auth.currentOrg.name }}</span>
        </div>
        <div class="row">
          <RouterLink to="/notifications" class="btn btn--ghost btn--sm" title="Уведомления">
            🔔 <span v-if="notifications.unread">{{ notifications.unread }}</span>
          </RouterLink>
          <RouterLink to="/profile" class="user">
            <strong>{{ auth.user?.full_name || auth.user?.email }}</strong>
            <span class="muted small">{{ roleText }}</span>
          </RouterLink>
          <button class="btn btn--ghost btn--sm" @click="onLogout">Выйти</button>
        </div>
      </header>

      <div v-if="auth.user && !auth.user.is_verified" class="container">
        <div class="alert alert--warning" style="margin-top: 16px">
          Email не подтверждён. Проверьте почту (локально — MailHog: http://localhost:8025).
          <RouterLink to="/profile" class="btn btn--ghost btn--sm">Отправить ещё раз</RouterLink>
        </div>
      </div>

      <main class="container content">
        <RouterView />
      </main>
    </div>
  </div>
</template>

<style scoped>
.layout {
  display: flex;
  min-height: 100vh;
}
.sidebar {
  width: var(--sidebar-width);
  flex-shrink: 0;
  background: var(--surface);
  border-right: 1px solid var(--border);
  padding: 16px 12px;
  position: sticky;
  top: 0;
  height: 100vh;
  overflow-y: auto;
}
.sidebar__logo {
  display: block;
  font-weight: 700;
  font-size: 18px;
  color: var(--text);
  text-decoration: none;
  padding: 4px 8px 16px;
}
.sidebar__group {
  margin-bottom: 14px;
}
.sidebar__title {
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  color: var(--muted);
  padding: 4px 8px;
}
.sidebar__link {
  display: flex;
  justify-content: space-between;
  padding: 7px 8px;
  border-radius: 6px;
  color: var(--text);
  text-decoration: none;
}
.sidebar__link:hover,
.sidebar__link.active {
  background: var(--bg);
}
.sidebar__link.active {
  font-weight: 600;
}
.count {
  background: var(--primary);
  color: var(--primary-text);
  border-radius: 999px;
  font-size: 12px;
  padding: 0 7px;
}
.main {
  flex: 1;
  min-width: 0;
}
.topbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 10px 16px;
  background: var(--surface);
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 10;
}
.org-select {
  width: auto;
  max-width: 260px;
}
.user {
  display: grid;
  text-align: right;
  color: var(--text);
  text-decoration: none;
  line-height: 1.2;
}
.content {
  padding-top: 24px;
  padding-bottom: 48px;
}
.burger {
  display: none;
}
@media (max-width: 860px) {
  .sidebar {
    position: fixed;
    left: 0;
    z-index: 40;
    transform: translateX(-100%);
    transition: transform 0.2s;
  }
  .sidebar.open {
    transform: none;
    box-shadow: 0 0 24px rgb(0 0 0 / 0.2);
  }
  .burger {
    display: inline-flex;
  }
  .user {
    display: none;
  }
}
</style>
