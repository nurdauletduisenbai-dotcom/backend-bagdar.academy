#!/bin/sh
set -e

# Миграции при старте контейнера (включено для сервиса backend, выключено для celery)
if [ "${DJANGO_MIGRATE:-0}" = "1" ]; then
    echo "→ Применяю миграции..."
    python manage.py migrate --noinput
fi

exec "$@"
