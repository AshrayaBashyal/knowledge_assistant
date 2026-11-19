#!/usr/bin/env bash
set -e

echo "Applying database migrations..."
python server/manage.py migrate

case "${CELERY_TASK_ALWAYS_EAGER:-True}" in
    1|[Tt][Rr][Uu][Ee]) EAGER_MODE=true ;;
    *) EAGER_MODE=false ;;
esac

if [ "$EAGER_MODE" = false ]; then
    if [ -z "$CELERY_REDIS_URL" ]; then
        echo "CELERY_TASK_ALWAYS_EAGER is disabled but CELERY_REDIS_URL is not set." >&2
        exit 1
    fi
    echo "Starting Celery worker in background (solo pool, concurrency=1)..."
    celery --workdir server -A config worker --pool=solo --concurrency=1 --loglevel=info &
else
    echo "Celery operating in in-process eager mode (0 external broker required)."
fi

echo "Starting Gunicorn web server..."
exec gunicorn --chdir server config.wsgi:application --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120
