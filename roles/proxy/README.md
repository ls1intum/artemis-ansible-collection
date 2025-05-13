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
```

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
```
