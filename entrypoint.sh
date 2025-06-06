#!/bin/sh
set -e

python manage.py migrate --noinput

python manage.py collectstatic --noinput

exec gunicorn newsroom.wsgi:application --bind 0.0.0.0:8000
