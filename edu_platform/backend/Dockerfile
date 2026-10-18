# EduPlatform Backend (Django 5 / DRF)
#   docker build --target dev  -> локальная разработка (runserver, pytest, ruff)
#   docker build --target prod -> продакшен (gunicorn)

# ---------- base: системные зависимости ----------
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
        libpq5 \
        curl \
    && rm -rf /var/lib/apt/lists/*

COPY docker/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# ---------- dev: + инструменты тестирования ----------
FROM base AS dev

COPY requirements.txt requirements-dev.txt ./
RUN pip install -r requirements-dev.txt

# Код монтируется volume-ом из docker-compose, копия нужна для запуска без volume
COPY . .

EXPOSE 8000
ENTRYPOINT ["/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# ---------- prod: только runtime-зависимости, без root ----------
FROM base AS prod

ENV DJANGO_SETTINGS_MODULE=config.settings.prod

COPY requirements.txt ./
RUN pip install -r requirements.txt

COPY . .

RUN useradd --create-home --uid 1000 app \
    && python manage.py collectstatic --noinput \
    && chown -R app:app /app
USER app

EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

ENTRYPOINT ["/entrypoint.sh"]
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "3"]
