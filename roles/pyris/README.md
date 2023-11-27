Pyris
=========

This role installs Pyris on a host. The role supports single node installations via Docker

Role Variables
--------------
Default variables can be found in the `defaults/main.yml` file.

### Variables that have to be configured for a single node installation:

```
pyris_deployment_user_public_key: #FIXME

pyris_config: #FIXME

proxy_ssl_certificate_path: #FIXME
proxy_ssl_certificate_key_path: #FIXME

```

pyris_config is the configuration for Pyris. See https://github.com/ls1intum/Pyris for details