# Django REST Framework + SimpleJWT Backend API

Полноценный, готовый к продакшену бэкенд на Python и Django c REST API (Django REST Framework), JWT-аутентификацией (djangorestframework-simplejwt), кастомной моделью пользователя, ролевой моделью, черным списком токенов (Token Blacklist), автоматической документацией Swagger/OpenAPI и набором автотестов.

---

## 🚀 Быстрый старт (Локально)

### 1. Клонирование и виртуальное окружение
```bash
# Перейдите в каталог проекта
cd django_backend

# Создайте и активируйте виртуальное окружение
python3 -m venv venv
source venv/bin/activate  # Для Linux / macOS
# venv\Scripts\activate   # Для Windows
```

### 2. Установка зависимостей
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Настройка переменных окружения
```bash
cp .env.example .env
```

### 4. Применение миграций и создание суперпользователя
```bash
python manage.py makemigrations accounts core_api
python manage.py migrate
python manage.py createsuperuser
```

### 5. Запуск сервера разработки
```bash
python manage.py runserver
```
Сервер будет доступен по адресу: `http://127.0.0.1:8000/`

---

## 🐳 Запуск через Docker & Docker Compose

```bash
docker compose up --build
```
Это запустит:
- Контейнер **web** (Django REST Framework на порту `8000`)
- Контейнер **db** (PostgreSQL 15 на порту `5432`)

---

## 🔐 Схема работы JWT (JSON Web Tokens)

1. **Регистрация** (`POST /api/v1/auth/register/`):
   Создает пользователя и сразу возвращает пару токенов: `access` и `refresh`.

2. **Получение токенов (Вход)** (`POST /api/v1/auth/token/`):
   Принимает `email` и `password`. Возвращает `access` (время жизни 15 минут) и `refresh` (время жизни 7 дней), а также данные пользователя. В полезную нагрузку (`payload`) токена зашиты `user_id`, `email`, `role`, `is_verified`.

3. **Защищенные запросы**:
   Клиент передает заголовок:
   ```http
   Authorization: Bearer <access_token>
   ```

4. **Обновление токена** (`POST /api/v1/auth/token/refresh/`):
   Когда access токен истекает (401 Unauthorized), клиент отправляет refresh токен и получает новый access токен. Включена ротация: старый refresh токен аннулируется и выдается новый.

5. **Выход из системы** (`POST /api/v1/auth/logout/`):
   Refresh токен вносится в таблицу черного списка (`token_blacklist`), блокируя дальнейшее использование.

---

## 📡 Таблица основных эндпоинтов API

| Метод | URL | Описание | Доступ |
|---|---|---|---|
| `POST` | `/api/v1/auth/register/` | Регистрация нового аккаунта | Любой |
| `POST` | `/api/v1/auth/token/` | Получение Access + Refresh токенов (Логин) | Любой |
| `POST` | `/api/v1/auth/token/refresh/` | Обновление истекшего Access токена | Любой |
| `POST` | `/api/v1/auth/token/verify/` | Проверка валидности любого токена | Любой |
| `GET` | `/api/v1/auth/profile/` | Получение профиля текущего пользователя | Bearer Token |
| `PUT / PATCH` | `/api/v1/auth/profile/` | Редактирование профиля | Bearer Token |
| `POST` | `/api/v1/auth/change-password/` | Смена пароля | Bearer Token |
| `POST` | `/api/v1/auth/logout/` | Выход с добавлением токена в Blacklist | Bearer Token |
| `GET` | `/api/v1/articles/` | Список статей с пагинацией и поиском | Любой |
| `POST` | `/api/v1/articles/` | Создание новой статьи | Bearer Token |
| `GET` | `/api/v1/articles/{id}/` | Детальный просмотр статьи | Любой |
| `PUT / PATCH` | `/api/v1/articles/{id}/` | Редактирование статьи | Только автор |
| `DELETE` | `/api/v1/articles/{id}/` | Удаление статьи | Только автор / Админ |
| `GET` | `/api/v1/articles/my/` | Список статей текущего автора | Bearer Token |
| `POST` | `/api/v1/articles/{id}/publish/` | Публикация черновика | Только автор |
| `GET` | `/api/docs/swagger/` | Интерактивная Swagger UI документация | Любой |
| `GET` | `/api/docs/redoc/` | ReDoc документация спецификации OpenAPI | Любой |

---

## 🧪 Запуск автоматических тестов

```bash
python manage.py test tests
```
Тесты проверяют:
- Регистрацию, выдачу токенов, авторизацию по заголовку `Authorization: Bearer <token>`
- Блокировку доступа при отсутствии токена (401)
- Работу ротации и черного списка токенов
- Разграничение прав доступа (автор vs посторонний пользователь)
