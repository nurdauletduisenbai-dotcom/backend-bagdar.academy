import { defineStore } from 'pinia'
import { ref } from 'vue'

export interface Toast {
  id: number
  text: string
  kind: 'success' | 'error' | 'info'
}

let nextId = 1

export const useToast = defineStore('toast', () => {
  const items = ref<Toast[]>([])

  function show(text: string, kind: Toast['kind'] = 'info', timeout = 4000) {
    const id = nextId++
    items.value.push({ id, text, kind })
    setTimeout(() => dismiss(id), timeout)
  }

  function dismiss(id: number) {
    items.value = items.value.filter((t) => t.id !== id)
  }

  return {
    items,
    dismiss,
    success: (text: string) => show(text, 'success'),
    error: (text: string) => show(text, 'error', 6000),
    info: (text: string) => show(text, 'info'),
  }
})
