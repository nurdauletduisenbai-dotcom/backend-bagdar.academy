import './assets/main.css'

import { createPinia } from 'pinia'
import { createApp } from 'vue'

import App from './App.vue'
import router from './router'
import { useAuthStore } from './stores/auth'

const app = createApp(App)
app.use(createPinia())

// Сначала восстанавливаем сессию, потом подключаем роутер — чтобы guard видел пользователя
useAuthStore()
  .restore()
  .finally(() => {
    app.use(router)
    app.mount('#app')
  })
