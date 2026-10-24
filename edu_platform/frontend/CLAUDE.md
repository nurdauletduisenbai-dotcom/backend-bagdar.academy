# Frontend EduPlatform: правила для Claude Code

Стек: **Vue 3 (Composition API, `<script setup lang="ts">`) + Vite + TypeScript + Pinia + Vue Router + axios**.
Бэкенд: Django REST API в `../backend` — готов полностью. **Источник правды по эндпоинтам — Swagger**
http://localhost:8000/docs/ (JSON-схема: http://localhost:8000/api/schema/). Перед вызовом нового эндпоинта
посмотри его запрос/ответ там и опиши тип в `src/types/api.ts`.

Демо-пользователи (после `make seed`): admin@fizmat.kz / AdminPassword123!, teacher@fizmat.kz / TeacherPassword123!,
student1@fizmat.kz / StudentPassword123!, parent@fizmat.kz / ParentPassword123!.

## Структура `src/`
- `api/http.ts`: единственный axios-инстанс. Добавляет `Authorization: Bearer` и `X-Org-ID`, при 401 один раз вызывает `/auth/refresh/` и повторяет запрос. Тут же `downloadFile()` (защищённые файлы) и `toFormData()` (загрузка). Не создавай другие axios-инстансы.
- `api/<домен>.ts`: запросы по доменам (`authApi`, `coursesApi`, `lessonsApi`, `testsApi`, `assignmentsApi`, `sessionsApi`, `paymentsApi`, `progressApi`, `orgsApi`…). Компоненты не вызывают `http` напрямую.
- `types/api.ts`: типы ответов API. Сверяй их с сериализаторами в `../backend/apps/*/serializers.py`.
- `stores/`: Pinia, setup-синтаксис. `auth` — пользователь, роли в текущей организации (`hasRole`, `isAdmin`, `isTeacher`, `isStaff`, `isStudent`, `isParent`), `switchOrg()`. `toast` — уведомления на экране. `notifications` — счётчик непрочитанных (опрос раз в 30 с).
- `composables/useAsync.ts`: `useAsync(fn)` — загрузка с `loading/error/data/run`; `useAction()` — `act(fn, 'Успех')` для кнопок (блокировка повторного нажатия + тосты).
- `composables/useYouTubeProgress.ts`: отправка прогресса просмотра видео через YouTube IFrame API.
- `layouts/AppLayout.vue` + `layouts/navigation.ts`: кабинет (верхнее меню), пункты фильтруются по ролям. Главная кабинета — **`/home`**.
- `layouts/PublicLayout.vue` + `views/public/`: публичный сайт без входа — `/` (лендинг: о платформе, новости, курсы, «как начать»; вошедшего перекидывает на `/home`), `/news`, `/news/:slug`. В шапке «Войти»/«Регистрация». Новости — `api/news.ts` (`/news/posts/`, `/news/stats/`), их ведёт суперпользователь в Django admin («Новости и статьи»). Текст поста — обычный текст, абзацы через пустую строку (без `v-html`).
- `router/index.ts`: `meta.public`, `meta.roles` — доступ к страницам по ролям.
- `components/ui/`: `AppModal`, `AppPager`, `AppBadge`, `StateBlock` (загрузка/ошибка/пусто), `PageHeader`, `ProgressBar`, `ToastHost`, `MathText` (формулы `$…$` через KaTeX).
- `views/`: `auth/`, `courses/`, `tests/`, `assignments/`, `progress/`, `teach/` (учитель), `admin/`; общие страницы — в корне.
- `demo.ts`: демо-аккаунты для кнопок быстрого входа (`VITE_SHOW_DEMO_ACCOUNTS=false` — скрыть).
- `assets/main.css`: дизайн-система **EdTeach** (Claude Design, проект «Education platform wireframes»): токены и базовые классы.
- `i18n/`: локализация (`vue-i18n`, composition-режим). См. раздел «Локализация» ниже.

## Локализация (RU / KK)
Языки: **қазақша** (`kk`, по умолчанию) и **русский** (`ru`, запасной — `fallbackLocale`). Третьего языка (EN) сейчас нет.
- `i18n/index.ts` — настройка `createI18n`, хранение выбора в `localStorage` (`edu_locale`), `setLocale()` ставит `<html lang>`.
- `i18n/locales/{kk,ru}.ts` — ключи сообщений, типизированные объекты (`as const`).
- `stores/locale.ts` — Pinia-обёртка (`useLocaleStore`): `current`, `options`, `select(locale)`. Читает/пишет `i18n.global` напрямую (не `useI18n()`), потому что используется и вне компонентов (например, `utils/format.ts`).
- `components/ui/LangSwitcher.vue` — переключатель ҚАЗ/RU (пропс `dark` для тёмного фона). Уже стоит в `AppLayout.vue` (шапка) и `AuthCard.vue` (страница входа/регистрации).
- `utils/format.ts` → `roleLabel(role)` — название роли на текущем языке (`roles.<role>` в локалях). Старый `roleLabels` (всегда RU) помечен `@deprecated`, оставлен для мест, ещё не переведённых.
- `layouts/navigation.ts` → `NavItem.labelKey` — ключ `nav.*`, не литеральный текст; в шаблоне `{{ $t(item.labelKey) }}`.

**Текущий статус (2026-10):** сделана только инфраструктура и каркас (навигация, меню пользователя, вход/регистрация, названия ролей) — **полный перевод всех экранов ещё не сделан**, это следующий шаг. Остальные страницы (каталог, уроки, тесты, админка и т.д.) пока на литеральном русском.

**Как переводить новый текст:** добавь ключ в оба файла `i18n/locales/{kk,ru}.ts` (не только в один — иначе `fallbackLocale` покажет русский для казахского), замени литерал в шаблоне на `{{ $t('раздел.ключ') }}` (или `:prop="$t(...)"` для атрибутов), для `<script setup>` — `const { t } = useI18n()`, вне компонентов — `i18n.global.t(...)` (как в `utils/format.ts`). Не переводи пользовательские данные с бэкенда (имена, названия курсов) — только статичный интерфейсный текст.

## Дизайн (EdTeach, вариант 1a вайрфреймов)
- **Цвета только через токены**: `--color-primary` (зелёный `#00ed64`, CTA), `--surface-dark`/`--teal-900` (тёмные полосы), `--text-strong/secondary/tertiary`, `--border-default/strong`, `--surface-subtle/soft/feature`, `--warning-*`, `--error-*`. Новые цвета не хардкодить.
- **Шрифты**: DM Sans (латиница, цифры) + Manrope (кириллица) — подключены через `@fontsource` в `main.css`.
- **Раскладка**: верхнее меню (`layouts/AppLayout.vue`, ≤5 пунктов на роль из `layouts/navigation.ts`), остальное — в меню аватара.
- **Классы**:
  - `btn` — зелёная «пилюля» (главное действие, одно на экран); `btn--ghost` — контур; `btn--text` — без рамки; `btn--dark`; `btn--danger`; размеры `btn--sm/--lg`, `btn--block`.
  - `band` — тёмная teal-полоса (шапка страницы, герой урока, итог теста); `page-band` — на всю ширину контейнера; внутри `eyebrow` (зелёный), `stat`, `muted`.
  - `card` (`--subtle`, `--feature`, `--warning`, `--dark`, `--flush`, `--link`), `pills` + `pill.active` (фильтры), `tabs` (вкладки с зелёным подчёркиванием), `side-nav` (вертикальное меню), `tag` + `tag--purple/orange/blue/pink/teal` (категория курса, цвет — `subjectTone()`), `badge--success/warning/danger/info/green`, `alert--*`, `dropzone` (пунктир «добавить/загрузить»), `list-lines`, `split` / `split--nav` (контент + боковая панель).
  - Компоненты: `AppIcon` (линейные иконки), `ProgressRing`, `ProgressBar`, `AppModal`, `StateBlock`, `PageHeader`, `MathText`.
- Ориентир по экранам — вайрфреймы: вход 2a, главная 1a/2r, каталог 2c, мои курсы 2e, курс 1j/1k, урок 1d, тест 1i/1g/1h, результат 2j, расписание 2g, задания 2h/2i, прогресс 2k/2l, входящие 2m, проверка 2n, банк вопросов 2o, редактор теста 2p, конструктор курса 1l, админка 2r–2u, профиль 2v, заказы 2w.

## Правила
- Импорты через алиас `@/` (это `src/`).
- Access-токен хранится только в памяти (`setAccessToken`). Refresh лежит в HttpOnly cookie, его ставит Django. Токены в localStorage не сохранять.
- Ошибки API приходят в формате `{ error: { code, message, details } }`. Для текста ошибки используй `errorMessage(e)` из `api/http.ts`.
- Списки пагинированы: `{ total, total_pages, page, page_size, results }` (тип `Paginated<T>`).
- Тексты интерфейса на русском (позже добавим i18n: ru / kk / en).
- Защищённые страницы: `meta: { requiresAuth: true }` в роуте.

## Роли и что строить
- Ученик: каталог и мои курсы, урок (видео через `/videos/{id}/play/`, материалы, комментарии), тесты
  (`/tests/{id}/attempts/` → ответы → submit), задания (`/assignments/{id}/submit/`), расписание, уведомления, прогресс.
- Учитель: конструктор курса (`/sections/`, `/lessons/`, `/videos/`, `/materials/`), банк вопросов, тесты
  (`/tests/`, `/tests/{id}/questions/`, `/stats/`), проверка заданий, посещаемость, прогресс учеников курса.
- Родитель: `/parents/children/`, `/progress/students/{id}/`.
- Админ: `/orgs/members/`, приглашения, заказы (`mark-paid`, `refund`), `/progress/org/summary/`, `/audit/logs/`.
- Файлы скачиваются только через `download_url` из ответа (с токеном), прямых ссылок на media нет.

## Проверка
- `npm run build`: проверка типов (`vue-tsc`) и сборка; должна проходить перед коммитом.
- `npm run dev`: http://localhost:5173, `/api` проксируется на `VITE_API_PROXY_TARGET` (по умолчанию `http://localhost:8000`).
- В Docker: `make up` из `edu_platform/`, затем `docker compose logs -f frontend`.
