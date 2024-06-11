#!/bin/bash

echo Waiting for DBs...
if ! wait-for-it --parallel --service redis-blender:6379; then
    exit
fi

celery --app=argon_server beat --loglevel=info --scheduler django_celery_beat.schedulers:DatabaseScheduler
