#!/bin/bash
set -e

# Load environment variables from .env if it exists
if [ -f .env ]; then
    # Export variables, filtering out comments and empty lines
    export $(grep -v '^#' .env | grep -v '^$' | xargs)
fi

# Generate IP allowlist YAML
if [ -z "$ALLOWED_IPS" ]; then
    echo "No IP restrictions configured - allowing access from everywhere"
    ALLOWED_IPS_YAML='          - "0.0.0.0/0"'
else
    echo "Configuring IP allowlist: $ALLOWED_IPS"
    ALLOWED_IPS_YAML=""
    IFS=',' read -ra IPS <<< "$ALLOWED_IPS"
    for ip in "${IPS[@]}"; do
        # Trim whitespace
        ip=$(echo "$ip" | xargs)
        ALLOWED_IPS_YAML="${ALLOWED_IPS_YAML}          - \"${ip}\"\n"
    done
    # Remove trailing newline
    ALLOWED_IPS_YAML=$(echo -e "$ALLOWED_IPS_YAML" | sed '$ d')
fi

# Generate config.yml from template
echo "Generating traefik/config.yml from template..."
while IFS= read -r line; do
    echo "$line" | sed "s|{{ALLOWED_IPS_YAML}}|${ALLOWED_IPS_YAML}|g"
done < traefik/config.yml.template > traefik/config.yml.tmp

mv traefik/config.yml.tmp traefik/config.yml

echo "Traefik configuration generated successfully!"
