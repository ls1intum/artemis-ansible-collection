#!/bin/bash
PROJECT_DIR="./Artemis/docker/"
COMPOSE_FILE="docker-compose.yml"
ENV_FILE="./.env"
ARGS="$@"

docker compose --project-directory $PROJECT_DIR -f $COMPOSE_FILE --env-file $ENV_FILE $ARGS