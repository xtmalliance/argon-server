#!/usr/bin/env bash

APP=argon-server

docker build --platform linux/amd64 -t "openskiessh/$APP" .
