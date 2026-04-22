#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

: "${DJANGO_SETTINGS_MODULE:=django_project.settings}"
: "${HOST:=0.0.0.0}"
: "${PORT:=8000}"
: "${WORKERS:=3}"

export DJANGO_SETTINGS_MODULE

log() { printf '\n\033[1;34m[deploy]\033[0m %s\n' "$*"; }

log "Установка зависимостей"
if command -v poetry >/dev/null 2>&1; then
    poetry install --no-interaction --no-root
    RUN="poetry run"
else
    pip install --upgrade pip
    pip install "Django>=5.0,<6.0" gunicorn
    RUN=""
fi

if ! $RUN python -c "import gunicorn" >/dev/null 2>&1; then
    log "Установка gunicorn"
    if [ -n "$RUN" ]; then
        poetry add gunicorn
    else
        pip install gunicorn
    fi
fi

log "Применение миграций"
$RUN python manage.py migrate --noinput

log "Сборка статики"
$RUN python manage.py collectstatic --noinput || true

log "Проверка проекта"
$RUN python manage.py check --deploy || true

log "Запуск Gunicorn на ${HOST}:${PORT} (workers=${WORKERS})"
exec $RUN gunicorn django_project.wsgi:application \
    --bind "${HOST}:${PORT}" \
    --workers "${WORKERS}" \
    --access-logfile - \
    --error-logfile -
