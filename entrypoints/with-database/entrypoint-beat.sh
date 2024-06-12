#!/bin/bash

echo Waiting for DBs...
if ! wait-for-it --parallel --service redis-argon-server-server:6379 --service db-argon-server:5432; then
    exit
fi

celery --app=argon_server beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
