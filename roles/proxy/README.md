# Proxy

This role sets up nginx as a proxy or load balancer for Artemis.

## Configuration

To configure the role, you need to set the required variables in your Ansible playbook or inventory. The following variables are required:

- `servers`: A list of server configurations, including name, SSL certificate path, SSL certificate key path, and whether it is the default server.
- `redirects`: A list of redirect configurations, including name, SSL certificate path, SSL certificate key path, whether it is the default server, and the target URL.
- `proxy_available_nodes`: A list of nodes for load balancing, either defined as a host-group or manually listed.
- `proxy_target_port`: The service port on nodes for load balancing.
- `proxy_forward_ssh`: Whether to enable port forwarding for SSH Git communication with Artemis ICL LocalVC.
- `proxy_node_protocol`: The protocol used to communicate with nodes (either http or https).
- `proxy_mailto`: A valid mail address used for the /mailto endpoint.
- `proxy_resolver`: The resolver configuration for nginx.
- `proxy_worker_rlmmiit_nofile`: The worker_rlimit_nofile setting for nginx.
- `proxy_worker_connections`: The worker_connections setting for nginx.
- `proxy_server_names_hash_bucket_size`: The server_names_hash_bucket_size setting for nginx.
- `proxy_generate_dh_param`: Whether to generate DH parameters.
- `proxy_send_timeout`: The send timeout for nginx.
- `proxy_read_timeout`: The read timeout for nginx.
- `fastcgi_send_timeout`: The send timeout for FastCGI.
- `fastcgi_read_timeout`: The read timeout for FastCGI.

Default variables can be found in the `defaults/main.yml` file.

### Variables that have to be configured:

```
servers: []
#   - name:
#     ssl_certificate_path:
#     ssl_certificate_key_path:
#     default_server: false

redirects: []
#   - name:
#     ssl_certificate_path:
#     ssl_certificate_key_path:
#     default_server: true
#     to: "{{ artemis_url }}"

# Nodes for load balancing; Either define a host-group or manually list all nodes
# proxy_available_nodes: "{{ groups.artemisnodes }}" # will not work anymore
proxy_available_nodes:
  - hostname: 127.0.0.1

# Service Port on nodes for load balancing; If differing for each node fall back to
# manual list of proxy_available_nodes and comment out proxy_target_port variable declaration
proxy_target_port: 8080

# Port forwarding configuration of Artemis nodes for SSH Git communication with Artemis ICL LocalVC
proxy_forward_ssh: true

# Protocol used to communicate with nodes (either http or https)
proxy_node_protocol: http

# Used for the /mailto enpoint - Has to be a valid mail address.
proxy_mailto:
# /etc/nginx/sites-available/artemis.conf
# Uncomment to change load balancing method from default (which is round robin)
# Can be "least_conn" or "ip_hash"
# proxy_load_balancing_method: ip_hash

proxy_resolver: "127.0.0.53 valid=300s"

proxy_worker_rlmmiit_nofile: 30000
proxy_worker_connections: 20000
proxy_server_names_hash_bucket_size: 256

proxy_generate_dh_param: true

proxy_send_timeout: "900s"
proxy_read_timeout: "900s"
fastcgi_send_timeout: "900s"
fastcgi_read_timeout: "900s"

# Health check settings
proxy_health_check_enabled: true
proxy_health_check_endpoint: "/ping"
proxy_health_check_interval: 2
proxy_health_check_timeout: 1
proxy_health_check_retries: 2
proxy_health_check_method: "systemd"  # or "lua"
```

## Active Health Checks

The proxy role includes active health checking to automatically detect and remove unresponsive upstream servers from the load balancing pool. This prevents user requests from hanging when a node freezes (e.g., due to GC pauses or process issues).

### Health Check Methods

Two methods are available:

| Method | Description | Requirements | Pros | Cons |
|--------|-------------|--------------|------|------|
| `systemd` (default) | External bash script runs periodically via systemd timer | Standard nginx | Simple, no special modules | Requires nginx reload on changes |
| `lua` | In-process health checks using Lua | OpenResty or nginx with lua-nginx-module | No reloads, faster failover | Requires OpenResty/Lua setup |

### Configuration

```yaml
# Enable/disable health checks (default: true)
proxy_health_check_enabled: true

# Health check endpoint on upstream servers (default: "/ping")
proxy_health_check_endpoint: "/ping"

# Interval between checks in seconds (default: 2)
proxy_health_check_interval: 2

# Timeout for each check in seconds (default: 1)
proxy_health_check_timeout: 1

# Number of retries before marking server down (default: 2)
proxy_health_check_retries: 2

# Health check method: "systemd" or "lua" (default: "systemd")
proxy_health_check_method: "systemd"
```

### Systemd Method

The systemd method uses a bash script that runs every `proxy_health_check_interval` seconds:

1. Probes each upstream server's `/ping` endpoint
2. If a server fails after `proxy_health_check_retries` attempts, marks it as `down` in the nginx config
3. Reloads nginx if the config changed
4. When server recovers, removes the `down` marker

**Monitoring:**
```bash
# Check timer status
systemctl status nginx-health-check.timer

# Watch health check logs
journalctl -t nginx-health-check -f

# View current upstream status
cat /etc/nginx/artemis-http-upstream.conf
```

### Lua Method

The Lua method runs health checks inside nginx worker processes:

1. Requires OpenResty or nginx compiled with lua-nginx-module
2. Health state stored in shared memory (`lua_shared_dict`)
3. Uses `balancer_by_lua_block` to route only to healthy backends
4. No config reloads needed - failover is immediate

**Monitoring:**
```bash
# Access the health status page (restricted to localhost and upstream nodes)
curl http://localhost/upstream-health
```

**Requirements for Lua method:**
- OpenResty (`apt install openresty`) OR
- nginx with lua-nginx-module and lua-resty-http

## Example Usage

Here is an example playbook:

```yaml
- hosts: proxy
  roles:
    - role: ls1intum.proxy
      vars:
        servers:
          - name: "example.com"
            ssl_certificate_path: "/etc/ssl/certs/example.com.crt"
            ssl_certificate_key_path: "/etc/ssl/private/example.com.key"
            default_server: true
        redirects:
          - name: "redirect.example.com"
            ssl_certificate_path: "/etc/ssl/certs/redirect.example.com.crt"
            ssl_certificate_key_path: "/etc/ssl/private/redirect.example.com.key"
            default_server: false
            to: "https://example.com"
        proxy_available_nodes:
          - hostname: "node1.example.com"
          - hostname: "node2.example.com"
        proxy_target_port: 8080
        proxy_forward_ssh: true
        proxy_node_protocol: http
        proxy_mailto: "admin@example.com"
        proxy_resolver: "127.0.0.53 valid=300s"
        proxy_worker_rlmmiit_nofile: 30000
        proxy_worker_connections: 20000
        proxy_server_names_hash_bucket_size: 256
        proxy_generate_dh_param: true
        proxy_send_timeout: "900s"
        proxy_read_timeout: "900s"
        fastcgi_send_timeout: "900s"
        fastcgi_read_timeout: "900s"
        # Health check configuration
        proxy_health_check_enabled: true
        proxy_health_check_method: "systemd"  # or "lua" for OpenResty
```

### Example with Lua Health Checks (OpenResty)

```yaml
- hosts: proxy
  roles:
    - role: ls1intum.proxy
      vars:
        servers:
          - name: "example.com"
            ssl_certificate_path: "/etc/ssl/certs/example.com.crt"
            ssl_certificate_key_path: "/etc/ssl/private/example.com.key"
            default_server: true
        proxy_available_nodes:
          - hostname: "node1.example.com"
          - hostname: "node2.example.com"
        proxy_target_port: 8080
        # Use Lua-based health checks (requires OpenResty)
        proxy_health_check_enabled: true
        proxy_health_check_method: "lua"
        proxy_health_check_interval: 2
        proxy_health_check_timeout: 1
        proxy_health_check_retries: 2
```
