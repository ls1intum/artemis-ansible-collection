# Artemis

This role installs Artemis on a host. The role supports single node installations as well as multi node installations.

## Role Variables and Configuration

Default variables can be found in the `defaults/main.yml` file.

### `artemis_version`

The deployed Artemis version. Accepted values:

- A [GitHub release tag](https://github.com/ls1intum/Artemis/releases) — either 3-segment (`9.1.2`) or 2-segment (`9.2`). The role downloads the matching `Artemis.war` from the GitHub release.
- An absolute path to a local `Artemis.war` (e.g. `/home/user/Artemis.war`). The role rsyncs it onto the target host.
- For Docker-based deployments (`use_docker: true`), the same string is used as the `ghcr.io/ls1intum/artemis:<tag>` image tag.

> **YAML quoting:** when recording a 2-segment version in YAML (`group_vars`, `host_vars`, JSON/YAML extra-vars), always quote it: `artemis_version: "9.2"`. Without quotes YAML parses `9.2` as a float, and values like `9.10` silently become `9.1`. The role asserts the value is a string at entry time and fails fast otherwise.

### Variables that have to be configured for a single node installation:

```
artemis_server_url: "https://artemis.example.com"
artemis_database_password: "your_database_password"

artemis_internal_admin_password: "your_admin_password"

proxy_ssl_certificate_path: "/path/to/ssl_certificate"
proxy_ssl_certificate_key_path: "/path/to/ssl_certificate_key"

artemis_jhipster_jwt: "your_jwt_secret"
```

The JWT secret can be generated with: `openssl rand -base64 64 | tr -d '\n'`.

### Additional Variables for external systems

To configure LDAP access for Artemis, add the following variables:
```
ldap:
  url: "ldaps://iauth.tum.de:636"
  user_dn: "cn=TUINI01-Artemis,ou=bindDNs,ou=iauth,dc=tum,dc=de"
  base: "ou=users,ou=data,ou=prod,ou=iauth,dc=tum,dc=de"
  password: "your_ldap_password"
```

To allow internal user registration:
```
user_management:
  registration:
    allowed_email_pattern:  ([a-zA-Z0-9_\-\.\+]+)@((tum\.de)|(in\.tum\.de)|(mytum\.de))
    allowed_email_pattern_readable: '@tum.de, @in.tum.de, @mytum.de'
    cleanup_time_minutes: 2
```

LocalVC configuration:
```
localvc:
  url: "https://artemis.example.com"
  repo_storage_base_path: "/path/to/repo_storage"
  use_version_control_access_token: false
  ssh_key_path: "/opt/artemis/ssh-keys" # Key path for the SSH host keys
  build_agent_use_ssh: true # Setting whether SSH should be used.
  ssh_url: "ssh://git@artemis.example.com:7921/" # URL template for SSH clone operations.
  build_agent_git_credentials:
    user: "build_agent_user"
    password: "build_agent_password"
  user: "localvc_user"
  password: "localvc_password"
```

LocalCI configuration:
```
continuous_integration:
  localci:
    is_core_node: true
    is_build_agent: true
    concurrent_build_size: 2
    thread_pool_size: 2
    proxy:
      http_proxy: "http://proxy:8080"
      https_proxy: "http://proxy:8080"
      no_proxy: "localhost"
    image_cleanup:
      expiry_days: 3
      schedule_time: "0 0 4 * * *"
```

Jenkins configuration:
```
continuous_integration:
  jenkins:
    url: "https://jenkins.example.com"
    user: "jenkins_user"
    password: "jenkins_password"
    secret_push_token: "jenkins_secret_push_token"
    vcs_credentials: "jenkins_vcs_credentials"
    artemis_auth_token_key: "jenkins_artemis_auth_token_key"
    artemis_auth_token_value: "jenkins_artemis_auth_token_value"
```

Athena configuration:
```
athena:
  url: "https://athena.example.com"
  secret: "athena_secret"
  restricted_modules: "module_text_llm,module_programming_llm" # optional parameter to restrict access to specific modules
```

Hyperion (Azure OpenAI / Spring AI) configuration:

Define two parts:
1. Configure Spring AI globally under `spring_ai:`.
2. Enable Hyperion via `artemis_hyperion_enabled: true` (sets `artemis.hyperion.enabled=true`).

```yaml
spring_ai:
  azure_openai:
    api_key: "{{ vault_azure_openai_api_key }}"
    endpoint: "https://my-azure-openai-resource.openai.azure.com/"
    deployment_name: "gpt-5-mini"
    temperature: 1.0

artemis_hyperion_enabled: true
```
Rendered into application-prod.yml under `spring_ai` and exported in `artemis.env` only if `spring_ai.azure_openai` is fully configured with non-empty `api_key`, `endpoint`, and `deployment_name`:

```text
spring.ai.model.chat = openai
spring.ai.openai.api-key
spring.ai.openai.base-url            # from spring_ai.azure_openai.endpoint
spring.ai.openai.microsoft-foundry   # default true
spring.ai.openai.timeout             # default 5m
spring.ai.openai.chat.model          # from spring_ai.azure_openai.deployment_name
spring.ai.openai.chat.temperature

artemis.hyperion.enabled
```

> The `spring_ai.azure_openai.*` inventory variables render the unified `spring.ai.openai.*` properties; the variable namespace is kept for backward compatibility.

Iris configuration:
```
iris:
  url: "https://iris.example.com"
  secret: "iris_secret"
```

Nebula configuration:
```
nebula:
  url: "https://nebula.example.com"
  secret: "nebula-secret"
```

Mail configuration:
```
mail:
  host: "smtp.example.com"
  port: 587
  user: "smtp_user"
  password: "smtp_password"
  protocol: "smtp"
  ssl_trust: "smtp.example.com"
```

LTI configuration:
```
lti:
  oauth_secret: "lti_oauth_secret"
```

### Additional Variables for multi node installations

Registry Configuration:
```
artemis_jhipster_registry_password: "your_registry_password" # Set this to the password for the JHipster registry in a multi-node setup
```
The Token can be generated with: `openssl rand -base64 64`

Active MQ configuration:
```
broker:
  url: "fcfe:0:0:0:0:0:b:1" # Default address in the wireguard network
  username: "brokeruser"
  password: "your_broker_password"
```

## Example Usage

Please refer to https://github.com/ls1intum/artemis-ansible for concrete examples.
