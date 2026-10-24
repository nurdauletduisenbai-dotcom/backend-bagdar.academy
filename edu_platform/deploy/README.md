# Сервер bagdar.academy

Raspberry Pi на Debian 13 (`nur@10.42.0.23`). Всё работает без Docker:

```text
nginx :80/:443 ─┬─ /            → /var/www/bagdar.academy/frontend   (собранный Vue)
                ├─ /static/     → /var/www/bagdar.academy/static     (collectstatic)
                └─ /api /admin /docs /health … → gunicorn 127.0.0.1:8000  (bagdar-backend)
Celery: bagdar-worker + bagdar-beat → Redis 127.0.0.1:6379
PostgreSQL 17 127.0.0.1:5432, база bagdar, роль bagdar
```

| Что | Где |
|---|---|
| Клон репозитория | `/home/nur/apps/backend-bagdar.academy` (ветка `main`) |
| Python venv | `/home/nur/apps/backend-bagdar.academy/venv` |
| Секреты (`.env`) | `/home/nur/apps/backend-bagdar.academy/edu_platform/.env`, шаблон — [env.prod.example](env.prod.example) |
| Загруженные файлы | `/var/lib/bagdar/media` |
| Юниты systemd | [systemd/](systemd/) → `/etc/systemd/system/` |
| nginx | [nginx/](nginx/) → `/etc/nginx/sites-available/bagdar.academy` + `snippets/bagdar-locations.conf` |

## Первая настройка (один раз)

```bash
cd ~/apps/backend-bagdar.academy && git pull
sudo bash edu_platform/deploy/setup.sh
```

Скрипт ставит Redis, Node.js и certbot, создаёт роль и базу PostgreSQL, генерирует `.env` с секретами,
ставит юниты systemd и сайт nginx, затем делает первый деплой. Повторный запуск безопасен.

Затем HTTPS — когда `bagdar.academy` и `www` указывают на внешний IP, а роутер пробрасывает 80 и 443 на `10.42.0.23`:

```bash
sudo bash edu_platform/deploy/setup.sh ssl
```

## Обновление (после релиза в `main`)

```bash
bash ~/apps/backend-bagdar.academy/edu_platform/deploy/deploy.sh
```

`git pull` → зависимости → сборка фронтенда → миграции → `collectstatic` → перезапуск сервисов → проверка `/ready/`.

## Диагностика

```bash
systemctl status bagdar-backend bagdar-worker bagdar-beat
journalctl -u bagdar-backend -f
sudo nginx -t && sudo tail -f /var/log/nginx/error.log
```
