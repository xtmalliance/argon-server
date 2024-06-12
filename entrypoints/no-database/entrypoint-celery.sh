#!/bin/bash

echo Waiting for DBs...
if ! wait-for-it --parallel --service redis-argon-server:6379; then
    exit
fi

celery --app=argon_server worker --loglevel=info
