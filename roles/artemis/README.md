# Artemis

This role installs Artemis on a host. The role supports single node installations as well as multi node installations.

## Role Variables and Configuration

Default variables can be found in the `defaults/main.yml` file.

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
  secret-token: "nebula-secret"
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
