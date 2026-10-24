# bagdar.academy — backend

Основной проект — **[`edu_platform/`](edu_platform/README.md)**: образовательная платформа.
Бэкенд — Django 5 + DRF, PostgreSQL, Redis, Celery; фронтенд — Vue 3 + Vite + TypeScript.

```text
.
├── edu_platform/   # платформа: backend/ (Django) + frontend/ (Vue 3) + docker-compose
├── archive/        # старые/демо-проекты, не используются (см. archive/README.md)
└── .github/        # CI: backend (ruff, миграции, pytest) и frontend (vue-tsc, build)
```

Быстрый старт: `cd edu_platform && make up`, подробности в [edu_platform/README.md](edu_platform/README.md).

**Как всё устроено** (архитектура, роли, процессы, схемы): [edu_platform/docs/ARCHITECTURE.md](edu_platform/docs/ARCHITECTURE.md).

## Ветки

| Ветка | Назначение |
|---|---|
| `main` | стабильная версия на сервере, обновляется только релизом (PR из `develop`) |
| `develop` | разработка — все изменения идут сюда |

Как разрабатывать, выпускать релизы и делать срочные исправления: [edu_platform/docs/BRANCHING.md](edu_platform/docs/BRANCHING.md).
