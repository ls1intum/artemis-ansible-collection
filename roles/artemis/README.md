Role Name
=========

This role installs artemis on a host. The role supports single node installations as well as multi node installations.

Role Variables
--------------
Default variables can be found in the `defaults/main.yml` file.

### Variables that have to be configured for a single node installation:

```
artemis_server_url: "https://artemis.example.de"
artemis_database_password: #FIXME
artemis_encryption_password: #FIXME

artemis_internal_admin_password: #FIXME

proxy_ssl_certificate_path:  #FIXME
proxy_ssl_certificate_key_path: #FIXME

```


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
    ci-token: # Jenkins secret push token
    health_api_token: # Access token for health API
    ssh_url: # Full SSH clone URL 
```
---


Jenkins configuration:
```
  jenkins:
    #TODO
```
---


Athene configuration:
```
athene:
  url:
  secret:
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
artemis_jhipster_jwt: #FIXME Multinode
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


