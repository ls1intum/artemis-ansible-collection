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

- **Operating System**: Ubuntu 20.04+ or Debian 11+
- **Docker Engine**: 20.10 or later
- **Docker Compose**: v2.0 or later
- **Ports**: 80, 443, and 50051 must be accessible from the internet
- **Resources**: Minimum 8GB RAM, 4 CPU cores recommended

### DNS Configuration

- A valid domain name pointing to your server's IP address
- DNS A record must be configured **before** running this role
- The domain must be publicly accessible for Let's Encrypt certificate validation

### Docker Installation

This role **does not** install Docker. You must install Docker and Docker Compose before running this role. You can:

1. Use a Docker installation role from Ansible Galaxy
2. Install manually: https://docs.docker.com/engine/install/
3. Use your organization's preferred Docker installation method

## Configuration

To configure the role, you need to set the required variables in your Ansible playbook or inventory.

### Required Variables

The following variables **must** be set:

```yaml
# Domain name for Weaviate instance
weaviate_domain: "weaviate.example.com"

# API key for authentication (generate with: openssl rand -base64 32)
weaviate_api_key: "your-secure-api-key-here"

# Email for Let's Encrypt certificate notifications
letsencrypt_email: "your-email@example.com"
```

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

```yaml
# Weaviate container resources
weaviate_cpu_limit: "8"
weaviate_memory_limit: "16G"

# Traefik resources
weaviate_traefik_cpu_limit: "1"
weaviate_traefik_memory_limit: "1G"

# Multi2vec-CLIP resources
weaviate_multi2vec_cpu_limit: "4"
weaviate_multi2vec_memory_limit: "8G"
```

## Example Usage

### Basic Single Node Installation

Here is an example playbook for a single node installation:

```yaml
- hosts: weaviate
  roles:
    - role: ls1intum.artemis.weaviate
      vars:
        weaviate_domain: "weaviate.example.com"
        weaviate_api_key: "your-secure-api-key-here"
        letsencrypt_email: "admin@example.com"
```

### Advanced Configuration with IP Whitelisting

```yaml
- hosts: weaviate
  roles:
    - role: ls1intum.artemis.weaviate
      vars:
        weaviate_domain: "weaviate.example.com"
        weaviate_api_key: "your-secure-api-key-here"
        letsencrypt_email: "admin@example.com"

        # Restrict access to private networks only
        weaviate_allowed_ips: "10.0.0.0/8,192.168.0.0/16,172.16.0.0/12"

        # Custom backup schedule (every 6 hours)
        weaviate_backup_schedule: "0 */6 * * *"
        weaviate_backup_retention_days: 14
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

## Security Considerations

### API Key Security

- Generate a strong API key: `openssl rand -base64 32`
- Store the API key in Ansible Vault, never in plain text
- Rotate API keys periodically
- Use different keys for different environments (dev, staging, prod)

### IP Whitelisting

By default, Weaviate is accessible from anywhere with valid API key authentication. For additional security:

```yaml
# Restrict to specific networks
weaviate_allowed_ips: "10.0.0.0/8,192.168.0.0/16"

# Restrict to single office IP
weaviate_allowed_ips: "203.0.113.42/32"
```

### SSL/TLS

- Let's Encrypt certificates are automatically managed by Traefik
- Certificates auto-renew before expiration
- TLS 1.2 minimum enforced
- Modern cipher suites only

### Rate Limiting

The role includes rate limiting middleware:
- Average: 100 requests/second
- Burst: 200 requests
- Adjust in `templates/config.yml.template.j2` if needed

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

This role was created by the [Chair of Applied Education Technologies at TUM](https://aet.cit.tum.de/).

For issues and contributions, please visit the [artemis-ansible-collection repository](https://github.com/ls1intum/artemis-ansible-collection).
