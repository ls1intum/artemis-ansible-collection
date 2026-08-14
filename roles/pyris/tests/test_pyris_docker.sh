#!/usr/bin/env bash
set -euo pipefail

TEST_DIR=$(mktemp -d)
trap 'rm -rf "$TEST_DIR"' EXIT

WORKING_DIR="$TEST_DIR/opt/pyris"
BIN_DIR="$TEST_DIR/bin"
LOG_FILE="$TEST_DIR/commands.log"
SCRIPT="$TEST_DIR/pyris-docker.sh"

mkdir -p "$WORKING_DIR" "$BIN_DIR"
touch "$WORKING_DIR/docker.env"
printf "PYRIS_DOCKER_TAG='initial'\n" > "$WORKING_DIR/runtime.env"

sed \
  -e "s|{{ pyris_repository_url }}|https://example.invalid/edutelligence.git|g" \
  -e "s|{{ pyris_repository_directory }}|$WORKING_DIR/edutelligence|g" \
  -e "s|{{ pyris_compose_file }}|pyris-production-external-weaviate.yml|g" \
  -e "s|{{ pyris_stable_env_file }}|$WORKING_DIR/docker.env|g" \
  -e "s|{{ pyris_runtime_env_file }}|$WORKING_DIR/runtime.env|g" \
  roles/pyris/templates/pyris-docker.sh.j2 > "$SCRIPT"
chmod +x "$SCRIPT"

cat > "$BIN_DIR/git" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
branch=
destination=${!#}
while (($#)); do
  if [[ "$1" == "--branch" ]]; then
    branch=$2
    shift 2
  else
    shift
  fi
done
printf 'git clone %s\n' "$branch" >> "$PYRIS_TEST_LOG"
mkdir -p "$destination/iris/docker"
touch "$destination/iris/docker/pyris-production-external-weaviate.yml"
printf '%s\n' "$branch" > "$destination/branch"
EOF

cat > "$BIN_DIR/docker" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail
printf 'docker %s\n' "$*" >> "$PYRIS_TEST_LOG"
EOF
chmod +x "$BIN_DIR/git" "$BIN_DIR/docker"

export PATH="$BIN_DIR:$PATH"
export PYRIS_TEST_LOG="$LOG_FILE"

# First adoption has no checkout. Restart must prepare the branch, skip stop,
# activate the checkout, and start the requested image.
"$SCRIPT" restart pr-699 pull/699
grep -qx 'pull/699' "$WORKING_DIR/edutelligence/branch"
grep -qx "PYRIS_DOCKER_TAG='pr-699'" "$WORKING_DIR/runtime.env"
if grep -q 'stop pyris-app' "$LOG_FILE"; then
  echo "First-adoption restart unexpectedly tried to stop a missing checkout" >&2
  exit 1
fi

# A subsequent deployment must clone and validate before stopping the current
# container, then activate and start the new branch/tag.
: > "$LOG_FILE"
"$SCRIPT" restart pr-700 pull/700
grep -qx 'pull/700' "$WORKING_DIR/edutelligence/branch"
grep -qx "PYRIS_DOCKER_TAG='pr-700'" "$WORKING_DIR/runtime.env"

clone_line=$(grep -n '^git clone pull/700$' "$LOG_FILE" | cut -d: -f1)
stop_line=$(grep -n 'stop pyris-app$' "$LOG_FILE" | cut -d: -f1)
start_line=$(grep -n 'up -d --pull always --no-build$' "$LOG_FILE" | cut -d: -f1)
if ! ((clone_line < stop_line && stop_line < start_line)); then
  echo "Restart did not prepare, stop, and start in the safe order" >&2
  exit 1
fi
