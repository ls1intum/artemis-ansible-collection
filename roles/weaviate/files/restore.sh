#!/bin/bash
set -e

# Check if backup ID is provided
if [ -z "$1" ]; then
    echo "Usage: ./restore.sh <backup-id>"
    echo ""
    echo "Available backups:"
    ls -1 backups/*.tar.gz 2>/dev/null | sed 's/backups\//  /' | sed 's/.tar.gz//' || echo "  No backups found"
    exit 1
fi

BACKUP_ID=$1
BACKUP_FILE="backups/${BACKUP_ID}.tar.gz"

# Check if backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    echo "Error: Backup file not found: $BACKUP_FILE"
    echo ""
    echo "Available backups:"
    ls -1 backups/*.tar.gz 2>/dev/null | sed 's/backups\//  /' | sed 's/.tar.gz//' || echo "  No backups found"
    exit 1
fi

echo "Starting Weaviate restore..."
echo "Backup ID: $BACKUP_ID"

# Load environment variables
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    exit 1
fi

export $(grep -v '^#' .env | grep -v '^$' | xargs)

# Check required variables
if [ -z "$WEAVIATE_API_KEY" ] || [ -z "$WEAVIATE_DOMAIN" ]; then
    echo "Error: WEAVIATE_API_KEY and WEAVIATE_DOMAIN must be set in .env"
    exit 1
fi

# Warning
echo ""
echo "WARNING: This will replace all current data with the backup!"
echo "Press Ctrl+C to cancel, or type 'yes' to continue..."
read -r CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Restore cancelled"
    exit 0
fi

# Extract backup
echo "Extracting backup..."
cd backups
tar -xzf ${BACKUP_ID}.tar.gz
cd ..

# Copy backup to container
echo "Copying backup to container..."
docker cp backups/${BACKUP_ID} weaviate:/var/lib/weaviate/backups/

# Initiate restore via Weaviate API
echo "Initiating restore..."
RESPONSE=$(curl -s -w "\n%{http_code}" -X POST \
    "https://${WEAVIATE_DOMAIN}/v1/backups/filesystem/${BACKUP_ID}/restore" \
    -H "Authorization: Bearer ${WEAVIATE_API_KEY}" \
    -H "Content-Type: application/json")

HTTP_CODE=$(echo "$RESPONSE" | tail -n1)
BODY=$(echo "$RESPONSE" | sed '$d')

if [ "$HTTP_CODE" != "200" ]; then
    echo "Error: Failed to initiate restore (HTTP $HTTP_CODE)"
    echo "$BODY"
    rm -rf backups/${BACKUP_ID}
    exit 1
fi

echo "Restore initiated successfully!"

# Poll restore status
echo "Waiting for restore to complete..."
MAX_RETRIES=60
RETRY_COUNT=0
STATUS=""

while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    sleep 5

    STATUS_RESPONSE=$(curl -s -w "\n%{http_code}" \
        "https://${WEAVIATE_DOMAIN}/v1/backups/filesystem/${BACKUP_ID}/restore" \
        -H "Authorization: Bearer ${WEAVIATE_API_KEY}")

    HTTP_CODE=$(echo "$STATUS_RESPONSE" | tail -n1)
    BODY=$(echo "$STATUS_RESPONSE" | sed '$d')

    if [ "$HTTP_CODE" == "200" ]; then
        STATUS=$(echo "$BODY" | grep -o '"status":"[^"]*' | cut -d'"' -f4)

        if [ "$STATUS" == "SUCCESS" ]; then
            echo "Restore completed successfully!"
            break
        elif [ "$STATUS" == "FAILED" ]; then
            echo "Error: Restore failed!"
            echo "$BODY"
            rm -rf backups/${BACKUP_ID}
            exit 1
        fi
    fi

    RETRY_COUNT=$((RETRY_COUNT + 1))
    echo "Restore in progress... (${RETRY_COUNT}/${MAX_RETRIES})"
done

if [ "$STATUS" != "SUCCESS" ]; then
    echo "Error: Restore timed out"
    rm -rf backups/${BACKUP_ID}
    exit 1
fi

# Cleanup
echo "Cleaning up..."
rm -rf backups/${BACKUP_ID}

echo ""
echo "Restore completed successfully!"
echo "  Backup ID: ${BACKUP_ID}"
echo ""
