#!/bin/bash

echo Waiting for DBs...
if ! wait-for-it --parallel --service redis-argon-server:6379 --service db-argon-server:5432; then
    exit
fi

# Collect static files
# echo "Collect static files"
# python manage.py collectstatic --noinput

# Apply database migrations
echo "Apply database migrations"
python manage.py migrate

# Start server
echo "Starting server"
gunicorn --bind :8000 --workers 3 argon_server.wsgi
