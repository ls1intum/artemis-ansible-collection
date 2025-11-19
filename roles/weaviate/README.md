# Weaviate

This role deploys a shared Weaviate vector database instance with Traefik reverse proxy and automatic HTTPS via Let's Encrypt. The role supports single node installations via Docker Compose.

## Description

This role sets up a production-ready Weaviate deployment that includes:

- **Weaviate**: Vector database for AI/ML applications
- **Traefik**: Reverse proxy with automatic SSL/TLS certificate management
- **Multi2vec-CLIP**: Vector embedding module for multimodal search
- **Automated Backups**: Configurable scheduled backups with retention policies
- **Security Features**: API key authentication, IP whitelisting, rate limiting, HTTPS enforcement

The setup is based on the [edutelligence repository](https://github.com/ls1intum/edutelligence) shared Weaviate infrastructure.

## Prerequisites

Before using this role, ensure the following requirements are met:

### System Requirements

- **Operating System**: Ubuntu 22.04 LTS+ or Debian 12+
- **Docker Engine**: 20.10 or later
- **Docker Compose**: v2.0 or later
- **Ports**: 80, 443, and 50051 must be accessible from the internet
- **Resources**:
  - **Development/Testing**: Minimum 8GB RAM, 4 CPU cores (uses default resource limits)
  - **Production**: 16GB+ RAM recommended, 6+ CPU cores (requires customizing resource limits)
  - See [Resource Planning](#resource-planning) section for detailed guidance

### DNS Configuration

- A valid domain name pointing to your server's IP address
- DNS A record must be configured **before** running this role
- The domain must be publicly accessible for Let's Encrypt certificate validation

### Docker Installation

This role **does not** install Docker. You must install Docker and Docker Compose before running this role. You can:

1. Use a Docker installation role from Ansible Galaxy
2. Install manually: [Docker installation docs](https://docs.docker.com/engine/install/)
3. Use your organization's preferred Docker installation method

## Configuration

### Required Variables

The following variables **must** be set in your playbook, inventory, or group_vars. The role will fail with a clear error message if any of these are missing or invalid.

#### `weaviate_domain` (required)

The fully qualified domain name for your Weaviate instance.

```yaml
weaviate_domain: "weaviate.example.com"
```

**Requirements:**
- Must be a valid domain name
- Must have a DNS A record pointing to your server's IP address
- Must be publicly accessible for Let's Encrypt certificate validation
- Cannot be `localhost` or an IP address (HTTPS requires a real domain)

**Examples:**
- ✓ `weaviate.example.com`
- ✓ `db.weaviate.example.org`
- ✗ `localhost` (won't work with Let's Encrypt)
- ✗ `192.168.1.100` (use a domain, not an IP)

#### `weaviate_api_key` (required)

A strong random API key for authenticating requests to Weaviate.

```yaml
# For production, use Ansible Vault:
weaviate_api_key: "{{ vault_weaviate_api_key }}"

# For testing only (generate a secure key):
weaviate_api_key: "dGhpcyBpcyBhIHNlY3VyZSBhcGkga2V5IGZvciBkZW1vIHB1cnBvc2VzIG9ubHk="
```

**Generate a secure API key:**
```bash
openssl rand -base64 32
```

**Security best practices:**
- Use a cryptographically secure random key (minimum 32 characters)
- **Always** store in Ansible Vault for production deployments
- Never commit plain-text API keys to version control
- Rotate keys periodically
- Use different keys for different environments (dev, staging, prod)

**Example Vault setup:**
```bash
# Create encrypted vault file
ansible-vault create group_vars/weaviate/vault.yml

# Add to vault.yml:
vault_weaviate_api_key: "your-generated-key-here"

# Reference in playbook:
weaviate_api_key: "{{ vault_weaviate_api_key }}"
```

#### `letsencrypt_email` (required)

Email address for Let's Encrypt certificate notifications.

```yaml
letsencrypt_email: "admin@example.com"
```

**Requirements:**
- Must be a valid email address (contains `@`)
- Should be actively monitored
- Used for certificate expiry notifications and renewal reminders

**Purpose:**
- Let's Encrypt sends important notifications about certificate expiry
- Required for automated certificate renewal
- Helps troubleshoot certificate issues

### Optional Variables

Default variables can be found in the [defaults/main.yml](defaults/main.yml) file. Key optional configurations:

#### Version and Paths

```yaml
weaviate_build_version: "1.30.0"
weaviate_working_directory: "/opt/weaviate"
```

#### User Management

```yaml
weaviate_user_name: "weaviate"
weaviate_user_uid: "1339"

# Optional deployment user with SSH access
weaviate_create_deployment_user: false
weaviate_deployment_user_name: "deployment"
weaviate_deployment_user_public_key: "ssh-rsa AAA..."
```

#### Security Configuration

```yaml
# Log level (trace, debug, info, warning, error, fatal, panic)
weaviate_log_level: "info"

# IP whitelisting (empty = accessible from everywhere with API key)
# Examples:
#   Single IP: "203.0.113.1/32"
#   Multiple: "10.0.0.0/8,192.168.0.0/16,172.16.0.0/12"
weaviate_allowed_ips: ""
```

#### Automated Backups

```yaml
# Enable automated backups
weaviate_enable_automated_backups: true

# Backup schedule (cron format) - default: daily at 2 AM
weaviate_backup_schedule: "0 2 * * *"

# Backup retention in days
weaviate_backup_retention_days: 7
```

#### Resource Limits

**Default values** are optimized for development/testing on modest hardware (8GB RAM total):

```yaml
# Traefik (reverse proxy - minimal requirements)
weaviate_traefik_cpu_limit: "1"
weaviate_traefik_memory_limit: "512M"
weaviate_traefik_cpu_reservation: "1"
weaviate_traefik_memory_reservation: "256M"

# Weaviate (vector database - scales with dataset size)
weaviate_cpu_limit: "2"
weaviate_memory_limit: "4G"
weaviate_cpu_reservation: "1"
weaviate_memory_reservation: "2G"

# Multi2vec-CLIP (ML model for embeddings)
weaviate_multi2vec_cpu_limit: "1"
weaviate_multi2vec_memory_limit: "2G"
weaviate_multi2vec_cpu_reservation: "1"
weaviate_multi2vec_memory_reservation: "1G"
```

**For production deployments**, increase these limits based on your workload. See [Resource Planning](#resource-planning) for recommendations.

## Example Usage

### Basic Single Node Installation

Here is an example playbook for a single node installation:

```yaml
- hosts: weaviate
  roles:
    - role: ls1intum.artemis.weaviate
      vars:
        weaviate_domain: "weaviate.example.com"
        weaviate_api_key: "{{ vault_weaviate_api_key }}"  # Store in Ansible Vault
        letsencrypt_email: "admin@example.com"
```

### Advanced Configuration with IP Whitelisting

```yaml
- hosts: weaviate
  roles:
    - role: ls1intum.artemis.weaviate
      vars:
        weaviate_domain: "weaviate.example.com"
        weaviate_api_key: "{{ vault_weaviate_api_key }}"
        letsencrypt_email: "admin@example.com"

        # Restrict access to private networks only
        weaviate_allowed_ips: "10.0.0.0/8,192.168.0.0/16,172.16.0.0/12"

        # Custom backup schedule (every 6 hours)
        weaviate_backup_schedule: "0 */6 * * *"
        weaviate_backup_retention_days: 14

        # Enable deployment user for CI/CD
        weaviate_create_deployment_user: true
        weaviate_deployment_user_public_key: "{{ vault_deployment_ssh_key }}"
```

### Inventory Example

```ini
[weaviate]
weaviate-prod.example.com

[weaviate:vars]
weaviate_domain=weaviate.example.com
letsencrypt_email=admin@example.com
```

## Post-Installation

### Verify Installation

After running the role, verify the installation:

1. **Check service status**:
   ```bash
   cd /opt/weaviate
   ./weaviate-docker.sh status
   ```

2. **View logs**:
   ```bash
   ./weaviate-docker.sh logs
   # Or for specific service:
   ./weaviate-docker.sh logs weaviate
   ```

3. **Test API access**:
   ```bash
   curl -H "Authorization: Bearer YOUR_API_KEY" \
        https://weaviate.example.com/v1/.well-known/ready
   ```

### Helper Script Commands

The role installs a helper script at `/opt/weaviate/weaviate-docker.sh` with the following commands:

```bash
./weaviate-docker.sh start           # Start all services
./weaviate-docker.sh stop            # Stop all services
./weaviate-docker.sh restart         # Restart all services
./weaviate-docker.sh logs [service]  # Show logs
./weaviate-docker.sh status          # Show service status
./weaviate-docker.sh backup          # Create manual backup
./weaviate-docker.sh restore <id>    # Restore from backup
```

## Backup and Restore

### Manual Backup

Create a manual backup:

```bash
cd /opt/weaviate
./backup.sh
```

Backups are stored in `/opt/weaviate/backups/` as compressed tar.gz files.

### Restore from Backup

List available backups:

```bash
cd /opt/weaviate
./restore.sh
```

Restore a specific backup:

```bash
./restore.sh backup-20240305-140530
```

**Warning**: Restoring a backup will replace all current data!

### Automated Backups

If `weaviate_enable_automated_backups` is enabled (default), backups run automatically according to `weaviate_backup_schedule`. Old backups are automatically deleted after `weaviate_backup_retention_days`.

View backup logs:

```bash
tail -f /opt/weaviate/backup.log
```

## Updating Weaviate

To update Weaviate to a new version:

1. **Update the version variable** in your playbook or inventory:
   ```yaml
   weaviate_build_version: "1.31.0"  # New version
   ```

2. **Re-run the Ansible playbook**:
   ```bash
   ansible-playbook -i inventory playbook.yml
   ```

3. **Verify the update**:
   ```bash
   cd /opt/weaviate
   ./weaviate-docker.sh logs weaviate
   ```

**Important Notes**:
- The Weaviate data volume persists across updates
- Weaviate handles schema migrations automatically on startup
- Always check [Weaviate release notes](https://github.com/weaviate/weaviate/releases) for breaking changes
- Consider creating a manual backup before major version upgrades (1.x → 2.x)

## Resource Planning

### Understanding Resource Requirements

The role's default resource limits are designed for **development and testing** environments on modest hardware. Production deployments require significantly more resources depending on your workload.

#### Default Resource Allocations (Development)

The default configuration totals:
- **CPU Limits**: 4 cores total
  - Traefik: 1 core
  - Weaviate: 2 cores
  - Multi2vec-CLIP: 1 core
- **CPU Reservations**: 2 cores guaranteed
  - Traefik: 1 core
  - Weaviate: 1 core
  - Multi2vec-CLIP: 1 core
- **Memory Limits**: 6.5GB total
  - Traefik: 512MB
  - Weaviate: 4GB
  - Multi2vec-CLIP: 2GB
- **Memory Reservations**: 3.25GB guaranteed
  - Traefik: 256MB
  - Weaviate: 2GB
  - Multi2vec-CLIP: 1GB

**Total System Requirements (Development)**: Minimum 8GB RAM, 4 CPU cores

**Note**: All CPU limits use integer values (whole cores) for clarity and predictable resource allocation.

### Production Resource Recommendations

For production deployments, adjust resource limits based on your expected workload:

#### Small Production (16GB RAM, 6 CPU cores)

Suitable for small teams, light usage, datasets < 100k vectors:

```yaml
# Weaviate
weaviate_cpu_limit: "4"
weaviate_memory_limit: "8G"
weaviate_cpu_reservation: "2"
weaviate_memory_reservation: "4G"

# Multi2vec-CLIP
weaviate_multi2vec_cpu_limit: "2"
weaviate_multi2vec_memory_limit: "4G"
weaviate_multi2vec_cpu_reservation: "1"
weaviate_multi2vec_memory_reservation: "2G"

# Traefik (can keep defaults)
weaviate_traefik_cpu_limit: "1"
weaviate_traefik_memory_limit: "512M"
```

**Total**: 7 CPU cores, ~12.5GB RAM

#### Medium Production (32GB RAM, 10 CPU cores)

Suitable for medium teams, moderate usage, datasets 100k-1M vectors:

```yaml
# Weaviate
weaviate_cpu_limit: "6"
weaviate_memory_limit: "12G"
weaviate_cpu_reservation: "3"
weaviate_memory_reservation: "6G"

# Multi2vec-CLIP
weaviate_multi2vec_cpu_limit: "3"
weaviate_multi2vec_memory_limit: "6G"
weaviate_multi2vec_cpu_reservation: "2"
weaviate_multi2vec_memory_reservation: "3G"

# Traefik
weaviate_traefik_cpu_limit: "1"
weaviate_traefik_memory_limit: "1G"
weaviate_traefik_cpu_reservation: "1"
weaviate_traefik_memory_reservation: "512M"
```

**Total**: 10 CPU cores, ~19GB RAM

#### Large Production (64GB+ RAM, 12+ CPU cores)

Suitable for large teams, heavy usage, datasets > 1M vectors:

```yaml
# Weaviate
weaviate_cpu_limit: "8"
weaviate_memory_limit: "16G"
weaviate_cpu_reservation: "4"
weaviate_memory_reservation: "8G"

# Multi2vec-CLIP
weaviate_multi2vec_cpu_limit: "4"
weaviate_multi2vec_memory_limit: "8G"
weaviate_multi2vec_cpu_reservation: "2"
weaviate_multi2vec_memory_reservation: "4G"

# Traefik
weaviate_traefik_cpu_limit: "1"
weaviate_traefik_memory_limit: "1G"
```

**Total**: ~13 CPU cores, ~25GB RAM

### Factors Affecting Resource Needs

#### Weaviate Memory Requirements

Weaviate's memory usage depends on:
- **Vector count**: ~50-100 bytes per vector (varies by dimensions)
- **Object properties**: Additional metadata increases memory
- **Index type**: HNSW indices use more memory than flat indices
- **Shard count**: Multiple shards increase overhead

**Rule of thumb**: Allocate 4GB + (vector_count × 100 bytes)

#### Multi2vec-CLIP Memory Requirements

The CLIP model requires:
- **Base model size**: ~600MB for ViT-B-32
- **Batch processing**: Additional memory for concurrent requests
- **Recommended**: 2GB minimum, 4-8GB for production

#### CPU Considerations

- **Weaviate**: CPU-intensive for:
  - Query processing and vector similarity calculations
  - Indexing new vectors
  - Background compaction
- **Multi2vec-CLIP**: CPU-only inference (no GPU support in default image)
  - Embedding generation is CPU-bound
  - More CPUs = faster embedding throughput

### Monitoring and Tuning

After deployment, monitor resource usage:

```bash
# Check container resource usage
docker stats

# Check Weaviate memory usage
./weaviate-docker.sh logs weaviate | grep -i memory

# View current limits
docker inspect weaviate | grep -A 10 "Memory"
```

**Signs you need more resources**:
- OOM (Out of Memory) kills in logs
- Query latency > 1 second for simple searches
- High CPU usage (> 80%) sustained
- Container restarts due to health check failures

### Example Production Playbook

```yaml
- hosts: weaviate_production
  roles:
    - role: ls1intum.artemis.weaviate
      vars:
        # Required
        weaviate_domain: "weaviate.production.example.com"
        weaviate_api_key: "{{ vault_weaviate_api_key }}"
        letsencrypt_email: "ops@example.com"

        # Production resource limits (medium tier)
        weaviate_cpu_limit: "6"
        weaviate_memory_limit: "12G"
        weaviate_cpu_reservation: "3"
        weaviate_memory_reservation: "6G"

        weaviate_multi2vec_cpu_limit: "3"
        weaviate_multi2vec_memory_limit: "6G"
        weaviate_multi2vec_cpu_reservation: "2"
        weaviate_multi2vec_memory_reservation: "3G"

        weaviate_traefik_cpu_limit: "1"
        weaviate_traefik_memory_limit: "1G"
        weaviate_traefik_cpu_reservation: "1"
        weaviate_traefik_memory_reservation: "512M"

        # Enable automated backups for production
        weaviate_enable_automated_backups: true
        weaviate_backup_schedule: "0 2 * * *"  # 2 AM daily
        weaviate_backup_retention_days: 30
```

## Security Considerations

### API Key Security

- Generate a strong API key: `openssl rand -base64 32`
- Store the API key in Ansible Vault, never in plain text
- Rotate API keys periodically
- Use different keys for different environments (dev, staging, prod)

### IP Whitelisting

By default, Weaviate is accessible from anywhere with valid API key authentication. For additional security, you can restrict access by IP address:

```yaml
# Restrict to specific networks
weaviate_allowed_ips: "10.0.0.0/8,192.168.0.0/16"

# Restrict to single office IP
weaviate_allowed_ips: "203.0.113.42/32"
```

**How it works**: The role uses Docker labels to configure Traefik's IP whitelist middleware dynamically. When `weaviate_allowed_ips` is set, the middleware is automatically enabled; when empty, public access (with API key) is allowed. This eliminates the need for manual Traefik configuration file editing.

### SSL/TLS

- Let's Encrypt certificates are automatically managed by Traefik
- Certificates auto-renew before expiration
- TLS 1.2 minimum enforced
- Modern cipher suites only

### Rate Limiting

The role includes rate limiting middleware:
- Average: 100 requests/second
- Burst: 200 requests
- Adjust in `templates/config.yml.j2` if needed

## Troubleshooting

### Certificate Issues

If Let's Encrypt certificate generation fails:

1. Verify DNS points to your server: `dig weaviate.example.com`
2. Check ports 80 and 443 are accessible from internet
3. View Traefik logs: `./weaviate-docker.sh logs traefik`
4. Delete `traefik/acme.json` and restart to retry

### Connection Issues

If unable to connect to Weaviate:

1. Check service status: `./weaviate-docker.sh status`
2. Verify health checks: `docker ps` (should show "healthy")
3. Check firewall rules allow ports 80, 443, 50051
4. Review logs: `./weaviate-docker.sh logs`

### High Memory Usage

Weaviate is configured with 16GB memory limit by default. If this is too high for your system:

```yaml
weaviate_memory_limit: "8G"
weaviate_memory_reservation: "4G"
```

### Backup Failures

If automated backups fail:

1. Check backup logs: `cat /opt/weaviate/backup.log`
2. Verify disk space: `df -h /opt/weaviate`
3. Test manual backup: `./backup.sh`
4. Check API key is correct in `.env`

## Files and Directories

After deployment, the following structure exists:

```
/opt/weaviate/
├── docker-compose.yml       # Docker Compose configuration
├── .env                     # Environment variables
├── weaviate-docker.sh       # Helper script
├── setup.sh                 # Setup script
├── backup.sh                # Backup script
├── restore.sh               # Restore script
├── generate-traefik-config.sh  # Traefik config generator
├── backup.log               # Backup logs
├── traefik/
│   ├── traefik.yml         # Traefik static configuration
│   ├── config.yml          # Traefik dynamic configuration
│   ├── config.yml.template # Template for config generation
│   └── acme.json           # Let's Encrypt certificates
└── backups/                 # Backup storage directory
    └── backup-*.tar.gz
```

## Related Documentation

- [Weaviate Documentation](https://weaviate.io/developers/weaviate)
- [Traefik Documentation](https://doc.traefik.io/traefik/)
- [edutelligence Repository](https://github.com/ls1intum/edutelligence) - Source of Weaviate setup
- [Let's Encrypt Documentation](https://letsencrypt.org/docs/)

## License

MIT

## Author Information

This role was created by the [Chair of Applied Software Engineering at TUM](https://aet.cit.tum.de/).

For issues and contributions, please visit the [artemis-ansible-collection repository](https://github.com/ls1intum/artemis-ansible-collection).
