import { onBeforeUnmount, type Ref } from 'vue'

import { videosApi } from '@/api/content'

interface YTPlayer {
  getCurrentTime(): number
  getPlayerState(): number
  destroy(): void
}

declare global {
  interface Window {
    YT?: { Player: new (el: HTMLIFrameElement, opts: object) => YTPlayer; PlayerState: { PLAYING: number } }
    onYouTubeIframeAPIReady?: () => void
  }
}

let apiPromise: Promise<void> | null = null

function loadApi(): Promise<void> {
  if (window.YT?.Player) return Promise.resolve()
  apiPromise ??= new Promise((resolve) => {
    window.onYouTubeIframeAPIReady = () => resolve()
    const script = document.createElement('script')
    script.src = 'https://www.youtube.com/iframe_api'
    document.head.appendChild(script)
  })
  return apiPromise
}

const REPORT_EVERY_MS = 10_000

/**
 * Отправляет на сервер прогресс просмотра, пока видео играет.
 * Сервер сам ограничивает прирост реальным временем — подделать прогресс не выйдет.
 */
export function useYouTubeProgress(onUpdate: (videoId: number, completed: boolean) => void) {
  let player: YTPlayer | null = null
  let timer: ReturnType<typeof setInterval> | null = null
  let currentVideo = 0

  async function attach(iframe: Ref<HTMLIFrameElement | null>, videoId: number) {
    detach()
    currentVideo = videoId
    await loadApi()
    if (!iframe.value || !window.YT) return
    player = new window.YT.Player(iframe.value, {})
    timer = setInterval(report, REPORT_EVERY_MS)
  }

  async function report() {
    if (!player || !window.YT) return
    try {
      if (player.getPlayerState() !== window.YT.PlayerState.PLAYING) return
      const result = await videosApi.progress(currentVideo, Math.floor(player.getCurrentTime()))
      onUpdate(currentVideo, result.is_completed)
    } catch {
      /* сеть/доступ: попробуем в следующий раз */
    }
  }

  function detach() {
    if (timer) clearInterval(timer)
    timer = null
    player = null
  }

  onBeforeUnmount(detach)
  return { attach, detach }
}

/** Добавляет к embed-URL параметры для управления плеером из JS */
export function withJsApi(embedUrl: string) {
  const url = new URL(embedUrl)
  url.searchParams.set('enablejsapi', '1')
  url.searchParams.set('origin', window.location.origin)
  return url.toString()
}
