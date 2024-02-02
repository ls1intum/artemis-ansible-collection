Artemis
=========

This role installs artemis on a host. The role supports single node installations as well as multi node installations.

Role Variables
--------------
Default variables can be found in the `defaults/main.yml` file.

### Variables that have to be configured for a single node installation:

```
artemis_server_url: "https://artemis.example.de"
artemis_database_password: #FIXME

artemis_internal_admin_password: #FIXME

proxy_ssl_certificate_path:  #FIXME
proxy_ssl_certificate_key_path: #FIXME

artemis_jhipster_jwt: #FIXME

```

The JWT secret can be generated with: `openssl rand -base64 64 | tr -d '\n'`.


### Additional Variables for external systems
To configure LDAP access for artemis, add the following variables:
```
ldap:
  url: "ldaps://iauth.tum.de:636"
  user_dn: "cn=TUINI01-Artemis,ou=bindDNs,ou=iauth,dc=tum,dc=de"
  base: "ou=users,ou=data,ou=prod,ou=iauth,dc=tum,dc=de"
  password:
```
---

To configure Jira as user management server add:

```
user_management:
  jira:
    url:
    user:
    password:
    admin_group: # Jira group that will have admin access in the artemis web ui
```

To allow internal user registration: 
```
user_management: 
  registration: 
    allowed_email_pattern:  ([a-zA-Z0-9_\-\.\+]+)@((tum\.de)|(in\.tum\.de)|(mytum\.de))
    allowed_email_pattern_readable: '@tum.de, @in.tum.de, @mytum.de'
    cleanup_time_minutes: 2
```
---

Bitbucket configuration:
```

bitbucket_hostname: bitbucket.example.com
version_control:
  bitbucket:
    url: "https://{{ bitbucket_hostname }}"
    ssh_url: "ssh://git@{{ bitbucket_hostname }}:7999"
    token:
```
---

Bamboo configuration:
```
continuous_integration:
  bamboo:
    url:
    token:
    bitbucket_link_name:
    result_plugin_token:
```
---

Gitlab configuration:
```
version_control:

  gitlab:
    url: 
    user: 
    password: 
    token: # Access token for $user
    ci_token: # Jenkins secret push token
    health_api_token: # Access token for health API
    ssh_url: # Full SSH clone URL 
```
---


Jenkins configuration:
```
  jenkins:
    url: 
    user: 
    password:
    secret_push_token:
    vcs_credentials:
    artemis_auth_token_key:
    artemis_auth_token_value:
```
---


Athena configuration:
```
athena:
  url:
  secret:
  restricted-modules: # optional parameter to restrict access to specific modules, e.g. module_text_llm,module_programming_llm
```
---

Apollon configuration:
```
apollon_url: #https://apollon.ase.in.tum.de/api/converter
```
---

Mail configuration:
```
mail:
  host:
  port:
  user:
  password:
  protocol:
  ssl_trust:
```

---

LTI configuration:
```
lti:
  oauth_secret:
```

### Additional Variables for multi node installtions

Registry Configuration:
```
artemis_jhipster_registry_password: #FIXME Multinode

```
The Token can be generated with: `openssl rand -base64 64`

---


Active MQ configuration
```
broker:
  url: "fcfe:0:0:0:0:0:b:1" # Default address in the wireguard network
  username: brokeruser
  password: #FIXME

```


