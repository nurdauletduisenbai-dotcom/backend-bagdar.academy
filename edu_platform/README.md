# EduPlatform Backend REST API (Python 3.12 / Django 5 / DRF)

Высоконагруженная серверная часть образовательной платформы для школ и учебных центров (видеоуроки YouTube unlisted, тесты с защитой от списывания, подготовка к экзаменам, кружки, многоарендность организаций, 2FA, Celery и ротация JWT).

---

## 1. Быстрый старт через Docker Compose

```bash
# 1. Склонируйте репозиторий и перейдите в каталог
cd edu_platform

# 2. Скопируйте файл переменных окружения
cp .env.example .env

# 3. Запустите все сервисы одной командой (API, PostgreSQL 16, Redis, MinIO, Celery, MailHog)
make up

# 4. Примените миграции и наполните базу демонстрационными данными
docker compose exec api python manage.py migrate
docker compose exec api python seed_data.py
```

Сервисы будут доступны по адресам:
- **REST API & Документация Swagger (OpenAPI 3.0):** [http://localhost:8000/docs/](http://localhost:8000/docs/)
- **Альтернативная документация ReDoc:** [http://localhost:8000/redoc/](http://localhost:8000/redoc/)
- **Health check:** `http://localhost:8000/health/`
- **MailHog (Тестирование писем):** [http://localhost:8025/](http://localhost:8025/)
- **MinIO S3 Web Console:** [http://localhost:9001/](http://localhost:9001/) (логин: `minioadmin` / пароль: `minioadmin`)

Демо-пользователи (создаются скриптом `seed_data.py`):
- **Администратор:** `admin@fizmat.kz` / `AdminPassword123!`
- **Учитель:** `teacher@fizmat.kz` / `TeacherPassword123!`
- **Ученик 1:** `student1@fizmat.kz` / `StudentPassword123!`
- **Ученик 2:** `student2@fizmat.kz` / `StudentPassword123!`
- **Родитель:** `parent@fizmat.kz` / `ParentPassword123!`

---

## 2. Локальный запуск без Docker

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python seed_data.py
python manage.py runserver
```

---

## 3. Архитектура проекта

Слоистая структура с четким разделением ответственности:

```text
edu_platform/
├── config/              # Конфигурация Django (base, dev, prod), urls, celery, wsgi, asgi
├── apps/
│   ├── common/          # Middleware (X-Request-ID, изоляция org_id), permissions, exceptions, pagination
│   ├── accounts/        # Кастомный User (AbstractBaseUser), сессии RefreshToken, EmailToken, 2FA, Argon2
│   ├── organizations/   # Организации, членство OrgMembership, инвайты Invite
│   ├── courses/         # Курсы (school_subject, exam_prep, club), группы, записи Enrollment
│   ├── content/         # Разделы Section, уроки Lesson, материалы S3, комментарии
│   ├── videos/          # YouTube видеоуроки, защищенный шлюз play, прогресс с порогом 90%
│   ├── questions/       # Дерево тем, банк вопросов (single, multi, short, number, match, open), LaTeX/Markdown
│   ├── assessments/     # Тесты, режимы, попытки, автопроверка закрытых вопросов, таймер, античит
│   ├── assignments/     # Домашние задания, сдача работ, оценки и отзывы учителей
│   ├── schedule/        # Расписание занятий групп, посещаемость
│   ├── progress/        # Аналитика успеваемости для ученика, родителя, учителя и админа
│   ├── notifications/   # Объявления, уведомления, асинхронные Celery-задачи отправки писем
│   ├── payments/        # Заказы, шлюзы Kaspi / Stripe, вебхуки, автозачисление
│   └── audit/           # Журнал аудита критических действий, соответствие GDPR
├── tests/               # Pytest-django тесты аутентификации, прав доступа и тестов
├── seed_data.py         # Скрипт генерации тестовых данных
├── Dockerfile           # Multi-stage сборка на базе python:3.12-slim
├── docker-compose.yml   # Оркестрация api, db, redis, worker, minio, mailhog
└── Makefile             # Удобные шорткаты: up, down, migrate, test, lint, seed
```

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
