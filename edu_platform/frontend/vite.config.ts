import { fileURLToPath, URL } from 'node:url'

import vue from '@vitejs/plugin-vue'
import { defineConfig, loadEnv } from 'vite'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  // Куда проксировать /api: локально — localhost:8000, в Docker — http://backend:8000
  const apiTarget = env.VITE_API_PROXY_TARGET || 'http://localhost:8000'

  return {
    plugins: [vue()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    server: {
      host: '0.0.0.0',
      port: 5173,
      strictPort: true,
      // Запросы идут на тот же origin, поэтому cookie с refresh-токеном работает без CORS
      proxy: {
        '/api': { target: apiTarget, changeOrigin: true },
      },
      // Надёжный HMR при монтировании кода в Docker на macOS/Windows
      watch: env.CHOKIDAR_USEPOLLING === 'true' ? { usePolling: true } : undefined,
    },
  }
})
