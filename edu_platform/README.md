# EduPlatform Backend REST API (Python 3.12 / Django 5 / DRF)

Высоконагруженная серверная часть образовательной платформы для школ и учебных центров (видеоуроки YouTube unlisted, тесты с защитой от списывания, подготовка к экзаменам, кружки, многоарендность организаций, 2FA, Celery и ротация JWT).

---

> 📘 **Полное описание архитектуры, ролей и процессов со схемами:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## 1. Структура

```text
edu_platform/
├── backend/             # Django 5 + DRF (Python 3.12)
│   ├── config/          # settings (base, dev, test, prod), urls, celery, wsgi/asgi
│   ├── apps/            # доменные приложения (см. ниже)
│   ├── tests/           # pytest-django
│   ├── docker/          # entrypoint.sh
│   ├── Dockerfile       # стадии dev / prod
│   ├── requirements.txt / requirements-dev.txt
│   └── seed_data.py     # демо-данные
├── frontend/            # Vue 3 + Vite + TypeScript + Pinia + Vue Router
│   ├── src/api/         # axios-клиент (JWT + авто-refresh), запросы к API
│   ├── src/stores/      # Pinia (auth)
│   ├── src/views/       # страницы
│   ├── Dockerfile       # стадии dev (Vite) / prod (nginx)
│   └── CLAUDE.md        # правила для разработки фронтенда через Claude Code
├── docker-compose.yml   # db, redis, backend, worker, beat, frontend, mailhog
├── .env.example         # общий шаблон переменных окружения
└── Makefile             # make up / down / logs / migrate / seed / test / lint
```

Приложения бэкенда (`backend/apps/`):

| Приложение | Назначение | API (`/api/v1/...`) |
|---|---|---|
| `common` | tenancy (X-Org-ID), JWT-аутентификация, базовые ViewSet, права, файлы, ошибки | — |
| `accounts` | пользователи, вход/refresh/сессии, 2FA, сброс пароля, родитель ↔ ученик | `auth/`, `parents/` |
| `organizations` | организации, участники и роли, приглашения | `orgs/` |
| `courses` | курсы, записи учеников, правила доступа (`access.py`) | `courses/` |
| `content` | разделы, уроки, материалы (файлы), комментарии | `sections/`, `lessons/`, `materials/`, `comments/` |
| `videos` | YouTube-видео, защищённый play, прогресс просмотра | `videos/` |
| `questions` | темы и банк вопросов организации | `topics/`, `questions/` |
| `assessments` | конструктор тестов, попытки, автопроверка, античит, статистика | `tests/` |
| `assignments` | домашние задания, сдача (текст/файл), проверка, напоминания | `assignments/`, `submissions/` |
| `schedule` | группы, занятия, посещаемость, напоминания | `groups/`, `sessions/`, `attendance/` |
| `progress` | прогресс по урокам/курсам, отчёты родителю и учителю, сводка админа | `progress/` |
| `notifications` | уведомления, настройки, объявления, письма (Celery) | `notifications/`, `announcements/` |
| `payments` | заказы, manual/Stripe, вебхук, автозачисление, возвраты | `payments/` |
| `audit` | журнал аудита организации | `audit/` |

Полный список эндпоинтов с примерами запросов — в Swagger: http://localhost:8000/docs/

Периодические задачи (сервис `beat`): напоминания о дедлайнах заданий (раз в час) и о занятиях (за 30 минут).

---|---|
| `common` | middleware (X-Request-ID, X-Org-ID), permissions, exceptions, pagination, soft delete |
| `accounts` | User (email-логин), refresh-сессии, email-токены, 2FA, Argon2 |
| `organizations` | организации, членство и роли, инвайты |
| `courses` | курсы, группы, записи на курс |
| `content` | разделы, уроки, материалы, комментарии |
| `videos` | YouTube-видео, защищённый play, прогресс |
| `questions` | темы и банк вопросов |
| `assessments` | тесты, попытки, автопроверка, античит |
| `assignments`, `schedule`, `progress`, `notifications`, `payments`, `audit` | пока только модели |

---

## 2. Запуск через Docker (рекомендуется)

```bash
cd edu_platform
make up          # = cp .env.example .env (если нет) + docker compose up -d --build
make seed        # демо-данные
make logs        # логи всех сервисов
```

Миграции применяются автоматически при старте контейнера `backend`.

| Сервис | Адрес |
|---|---|
| Frontend (Vue, HMR) | http://localhost:5173 |
| API + Swagger (все эндпоинты) | http://localhost:8000/docs/ (корень `/` ведёт сюда же) |
| ReDoc | http://localhost:8000/redoc/ |
| Health / Ready | http://localhost:8000/health/, `/ready/` |
| MailHog (письма) | http://localhost:8025 |
| PostgreSQL 16 | `localhost:5432` (postgres / postgres) |

Фронтенд обращается к `/api/...` на своём же адресе, Vite проксирует запросы на Django. Поэтому CORS не нужен, а refresh-cookie работает.

Демо-пользователи (после `make seed`; на странице входа есть кнопки быстрого входа):

| Роль | Email | Пароль | Что проверить |
|---|---|---|---|
| Администратор | `admin@fizmat.kz` | `AdminPassword123!` | сводка, участники и роли, приглашения, подтверждение оплат, аудит |
| Учитель | `teacher@fizmat.kz` | `TeacherPassword123!` | редактор курса, видео/материалы, тесты и банк вопросов, проверка работ, посещаемость |
| Куратор | `curator@fizmat.kz` | `CuratorPassword123!` | просмотр курсов и прогресса учеников |
| Ученик | `student1@fizmat.kz` | `StudentPassword123!` | уроки, видео, тесты, сдача заданий, расписание |
| Ученик 2 | `student2@fizmat.kz` | `StudentPassword123!` | покупка курса (заказ ждёт подтверждения админом) |
| Родитель | `parent@fizmat.kz` | `ParentPassword123!` | прогресс ребёнка (student1) |
| Две школы | `multi@fizmat.kz` | `MultiPassword123!` | переключатель организаций: ученик в ФизМат, учитель в Школе №2 |
| Админ Школы №2 | `admin@school2.kz` | `School2Password123!` | изоляция: данных ФизМат не видно |
| Django admin | `superadmin@edu.local` | `SuperAdminPassword123!` | http://localhost:8000/admin/ |

---

## 3. Запуск без Docker

```bash
cd edu_platform && cp .env.example .env     # Postgres и Redis должны быть запущены локально

# backend
cd backend
python3.12 -m venv venv && source venv/bin/activate
pip install -r requirements-dev.txt
python manage.py migrate && python seed_data.py
python manage.py runserver

# frontend (в другом терминале)
cd edu_platform/frontend
npm install
npm run dev
```

Тесты бэкенда не требуют Redis (`config.settings.test` использует locmem-кэш):
`cd backend && pytest`.

---

## 4. Матрица прав доступа: «Роль × Действие» (RBAC)

| Действие / Ресурс | Гость | Ученик (Student) | Родитель (Parent) | Учитель (Teacher) | Куратор (Curator) | Администратор (Admin) |
|---|---|---|---|---|---|---|
| Просмотр каталога опубликованных курсов |  |  |  |  |  |  |
| Регистрация по email (POST /auth/register) |  |  |  | ❌ (только инвайт/админ) | ❌ | ❌ |
| Просмотр закрытого урока и видео | ❌ |  (только активная запись) | ❌ |  (свои курсы) |  |  |
| Просмотр бесплатного превью (is_free_preview) |  |  |  |  |  |  |
| Сдача теста и автосохранение ответов | ❌ |  (только свой тест) | ❌ | ❌ | ❌ | ❌ |
| Просмотр правильных ответов до сдачи | ❌ | ❌ (запрещено) | ❌ |  |  |  |
| Просмотр прогресса и результатов ребенка | ❌ | ❌ |  (только свои дети) | ❌ | ❌ |  |
| Создание и редактирование курсов | ❌ | ❌ | ❌ |  (в рамках школы) | ❌ |  |
| Проверка открытых вопросов и заданий | ❌ | ❌ | ❌ |  | ❌ |  |
| Управление пользователями и ролями | ❌ | ❌ | ❌ | ❌ | ❌ |  (своя организация) |
| Доступ к данным чужой организации | ❌ | ❌ (404/403) | ❌ (404/403) | ❌ (404/403) | ❌ (404/403) | ❌ (404/403) |

---

## 5. Принятые по умолчанию инженерные решения

1. **Многоарендность (Tenant Isolation):**
   - Передается через заголовок `X-Org-ID` либо извлекается из JWT полезной нагрузки. Любые запросы к курсам, пользователям, тестам строго изолируются. Доступ к объектам другой организации возвращает 404/403.
2. **Безопасность видео:**
   - В открытых списках уроков `youtube_video_id` намеренно не отдается клиенту. Единственный способ проигрывания — эндпоинт `GET /api/v1/videos/{id}/play/`, который возвращает безопасный embed на `youtube-nocookie.com` только после проверки активной записи или флага `is_free_preview`.
3. **Защита от списывания в тестах:**
   - Клиент никогда не получает флаги `is_correct` и разборы решений до завершения и отправки теста.
   - Сервер фиксирует события `tab_blur`, `window_resize` и `copy_paste`.
   - Серверный таймер блокирует и автоматически закрывает просроченные попытки.
4. **Ротация токенов и Anti-Theft:**
   - При каждом вызове `/auth/refresh/` старый refresh-токен помечается использованным, а клиенту выдается новый. Если злоумышленник пытается повторно отправить уже сгоревший токен, сервер отзывает **все активные сессии пользователя**.
5. **Многоязычность:**
   - Поддерживаются локали `ru` (Русский), `kk` (Қазақша), `en` (English).

---

## 6. Запуск тестов и линтеров

```bash
# Запуск тестов
make test

# Запуск линтеров
make lint
```
