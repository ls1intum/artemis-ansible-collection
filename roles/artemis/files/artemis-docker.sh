#!/bin/bash

PROJECT_DIR="./Artemis/docker/"
COMPOSE_FILE="docker-compose.yml"
ENV_FILE="./.env"

# Function: Print general usage information
function general_help {
    cat << HELP
Usage:
  ./$(basename "$0") <command> [options]

Commands:
  start <pr_tag> <pr_branch>      Start Artemis, Nginx and the database
  stop                            Stop the Artemis server. Nginx and database will remain started
  restart <pr_tag> <pr_branch>    Restart the Artemis server. Nginx and database are unaffected
  run <docker compose cmd>        Run any docker compose subcommand of your choice
HELP
}

function start {
  local pr_tag=$1
  local pr_branch=$2

  echo "Starting Artemis with PR tag: $pr_tag and branch: $pr_branch"
  rm -rf Artemis
  git clone https://github.com/ls1intum/Artemis.git -b "$pr_branch" Artemis
  sed -i "s/ARTEMIS_TAG=\".*\"/ARTEMIS_TAG=\"$pr_tag\"/g" .env
  docker compose --project-directory "$PROJECT_DIR" -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d --pull always --no-build
}

function stop {
  # TODO: In the future extract pr_tag and pr_branch from env

  echo "Stopping Artemis"
  docker compose --project-directory "$PROJECT_DIR" -f "$COMPOSE_FILE" --env-file "$ENV_FILE" stop artemis-app
}

function restart {
    stop "$@"
    start "$@"
}

function run_docker_compose_cmd {
   docker compose --project-directory "$PROJECT_DIR" -f "$COMPOSE_FILE" --env-file "$ENV_FILE" "$@"
}

# read subcommand `artemis-docker subcommand server` in variable and remove base command from argument list
subcommand=$1; shift

# Handle empty subcommand
if [ -z "$subcommand" ]; then
    general_help
    exit 1
fi

case "$subcommand" in
    start)
        start "$@"
        ;;
    stop)
        stop "$@"
        ;;
    restart)
        restart "$@"
        ;;
    run)
        run_docker_compose_cmd "$@"
        ;;
    *)
        printf "Invalid Command: $subcommand\n\n" 1>&2
        general_help
        exit 1
        ;;
esac