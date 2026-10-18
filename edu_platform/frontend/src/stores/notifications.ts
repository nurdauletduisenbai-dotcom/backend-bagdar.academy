import { defineStore } from 'pinia'
import { ref } from 'vue'

import { notificationsApi } from '@/api/notifications'

const POLL_MS = 30_000

export const useNotificationsStore = defineStore('notifications', () => {
  const unread = ref(0)
  let timer: ReturnType<typeof setInterval> | null = null

  async function refresh() {
    try {
      unread.value = (await notificationsApi.unreadCount()).unread
    } catch {
      /* не критично: счётчик обновится при следующем опросе */
    }
  }

  function start() {
    stop()
    refresh()
    timer = setInterval(refresh, POLL_MS)
  }

  function stop() {
    if (timer) clearInterval(timer)
    timer = null
  }

  return { unread, refresh, start, stop }
})
