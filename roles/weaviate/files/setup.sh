#!/bin/bash
set -e

echo "Setting up Weaviate deployment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "Error: .env file not found!"
    echo "Please copy .env.example to .env and configure it."
    exit 1
fi

# Create acme.json for Let's Encrypt certificates if it doesn't exist
if [ ! -f traefik/acme.json ]; then
    echo "Creating traefik/acme.json..."
    touch traefik/acme.json
    chmod 600 traefik/acme.json
fi

# Generate Traefik configuration from template
echo "Generating Traefik configuration..."
./generate-traefik-config.sh

echo ""
echo "Setup complete!"
echo ""
echo "IMPORTANT: Before starting, ensure:"
echo "  1. Your DNS records point to this server"
echo "  2. Ports 80, 443, and 50051 are accessible"
echo "  3. Your .env file has secure credentials"
echo ""
echo "You can now start Weaviate with: docker-compose up -d"
