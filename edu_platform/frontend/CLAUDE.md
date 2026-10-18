# Frontend EduPlatform: правила для Claude Code

Стек: **Vue 3 (Composition API, `<script setup lang="ts">`) + Vite + TypeScript + Pinia + Vue Router + axios**.
Бэкенд: Django REST API в `../backend`, документация OpenAPI на http://localhost:8000/docs/.

## Структура `src/`
- `api/http.ts`: единственный axios-инстанс. Добавляет `Authorization: Bearer` и `X-Org-ID`, при 401 один раз вызывает `/auth/refresh/` и повторяет запрос. Не создавай другие axios-инстансы.
- `api/<домен>.ts`: функции запросов по доменам (`authApi`, `coursesApi`, …). Компоненты не вызывают `http` напрямую.
- `types/api.ts`: типы ответов API. Сверяй их с сериализаторами в `../backend/apps/*/serializers.py`.
- `stores/`: Pinia, setup-синтаксис (`defineStore('id', () => {...})`).
- `views/`: страницы (подключаются в `router/index.ts` через lazy `import()`), `components/`: переиспользуемые части.
- `assets/main.css`: CSS-переменные (`--bg`, `--surface`, `--text`, `--primary` …) с тёмной темой. Используй их, а не хардкод цветов.

## Правила
- Импорты через алиас `@/` (это `src/`).
- Access-токен хранится только в памяти (`setAccessToken`). Refresh лежит в HttpOnly cookie, его ставит Django. Токены в localStorage не сохранять.
- Ошибки API приходят в формате `{ error: { code, message, details } }`. Для текста ошибки используй `errorMessage(e)` из `api/http.ts`.
- Списки пагинированы: `{ total, total_pages, page, page_size, results }` (тип `Paginated<T>`).
- Тексты интерфейса на русском (позже добавим i18n: ru / kk / en).
- Защищённые страницы: `meta: { requiresAuth: true }` в роуте.

## Проверка
- `npm run build`: проверка типов (`vue-tsc`) и сборка; должна проходить перед коммитом.
- `npm run dev`: http://localhost:5173, `/api` проксируется на `VITE_API_PROXY_TARGET` (по умолчанию `http://localhost:8000`).
- В Docker: `make up` из `edu_platform/`, затем `docker compose logs -f frontend`.
