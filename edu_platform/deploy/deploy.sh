#!/usr/bin/env bash
# Обновить сервер до свежей версии из GitHub (запускать от пользователя nur, без sudo):
#   bash ~/apps/backend-bagdar.academy/edu_platform/deploy/deploy.sh          # ветка main
#   bash ~/apps/backend-bagdar.academy/edu_platform/deploy/deploy.sh develop  # другая ветка
set -euo pipefail

BRANCH="${1:-main}"
REPO_DIR=/home/nur/apps/backend-bagdar.academy
VENV="$REPO_DIR/venv"
WEB_ROOT=/var/www/bagdar.academy
export DJANGO_SETTINGS_MODULE=config.settings.prod

step() { printf '\n\033[1;34m→ %s\033[0m\n' "$*"; }

step "Код: $BRANCH"
cd "$REPO_DIR"
git fetch origin
git checkout "$BRANCH"
git pull --ff-only origin "$BRANCH"
git log --oneline -1

step "Python-зависимости"
[ -x "$VENV/bin/python" ] || python3 -m venv "$VENV"
"$VENV/bin/pip" install -q --upgrade pip
"$VENV/bin/pip" install -q -r edu_platform/backend/requirements.txt

step "Фронтенд: сборка"
cd "$REPO_DIR/edu_platform/frontend"
npm ci --no-audit --no-fund
npm run build
rsync -a --delete dist/ "$WEB_ROOT/frontend/"

step "Миграции и статика"
cd "$REPO_DIR/edu_platform/backend"
"$VENV/bin/python" manage.py migrate --noinput
"$VENV/bin/python" manage.py collectstatic --noinput -v 0
"$VENV/bin/python" manage.py check --deploy --fail-level ERROR

step "Перезапуск сервисов"
sudo /usr/bin/systemctl restart bagdar-backend bagdar-worker bagdar-beat

step "Проверка"
for _ in $(seq 1 20); do
    if curl -fsS -H 'Host: bagdar.academy' -H 'X-Forwarded-Proto: https' http://127.0.0.1:8000/ready/; then
        printf '\n\033[1;32m✓ Готово: %s\033[0m\n' "$(git -C "$REPO_DIR" log --oneline -1)"
        exit 0
    fi
    sleep 1
done
echo "✗ Бэкенд не ответил. Логи: journalctl -u bagdar-backend -n 50" >&2
exit 1
