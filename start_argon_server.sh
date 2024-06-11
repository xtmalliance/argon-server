#!/bin/bash
ARGON_SERVER_ROOT=.
cp .env.sample .env
chmod +x $ARGON_SERVER_ROOT/entrypoints/with-database/entrypoint.sh
STATUS="$(systemctl is-active postgresql)"
if [ "${STATUS}" = "active" ]; then
    echo "stop local instance of postgresql"
    sudo systemctl stop postgresql
fi
docker-compose down
docker rm -f $(docker ps -a -q)
docker volume rm $(docker volume ls -q)
cd $ARGON_SERVER_ROOT
docker-compose up
