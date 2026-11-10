#!/usr/bin/env bash
set -e

echo "Applying database migrations..."
python server/manage.py migrate

# If Redis is configured and eager mode is disabled, start background Celery worker concurrently
if [ "$CELERY_TASK_ALWAYS_EAGER" != "True" ] && [ -n "$CELERY_REDIS_URL" ]; then
    echo "Starting Celery worker in background (concurrency=1)..."
    celery --workdir server -A config worker --concurrency=1 --loglevel=info &
else
    echo "Celery operating in in-process eager mode (0 external broker required)."
fi

echo "Starting Gunicorn web server..."
exec gunicorn --chdir server config.wsgi:application --bind 0.0.0.0:$PORT --workers 2 --threads 4 --timeout 120
