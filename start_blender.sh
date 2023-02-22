#!/bin/bash
BLENDER_ROOT=.
cp .env.sample .env
chmod +x $BLENDER_ROOT/entrypoint.sh
docker-compose down
docker rm -f $(docker ps -a -q)
docker volume rm $(docker volume ls -q)
cd $BLENDER_ROOT
docker-compose up
