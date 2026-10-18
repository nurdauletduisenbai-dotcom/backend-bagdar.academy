import { ref, type Ref } from 'vue'

import { errorMessage } from '@/api/http'
import { useToast } from '@/stores/toast'

/**
 * Загрузка данных со статусами loading / error.
 *   const { data, loading, error, run } = useAsync(() => coursesApi.list())
 */
export function useAsync<T>(fn: () => Promise<T>, options: { immediate?: boolean } = {}) {
  const data = ref<T | null>(null) as Ref<T | null>
  const loading = ref(false)
  const error = ref('')

  async function run() {
    loading.value = true
    error.value = ''
    try {
      data.value = await fn()
    } catch (e) {
      error.value = errorMessage(e)
    } finally {
      loading.value = false
    }
    return data.value
  }

  if (options.immediate !== false) run()
  return { data, loading, error, run }
}

/**
 * Обёртка для действий (кнопки «Сохранить», «Удалить»): блокирует повторное нажатие,
 * показывает тост об успехе или ошибке.
 */
export function useAction() {
  const busy = ref(false)
  const toast = useToast()

  async function act<T>(fn: () => Promise<T>, success?: string): Promise<T | undefined> {
    if (busy.value) return
    busy.value = true
    try {
      const result = await fn()
      if (success) toast.success(success)
      return result
    } catch (e) {
      toast.error(errorMessage(e))
    } finally {
      busy.value = false
    }
  }

  return { busy, act }
}
