# Pyris

This role provisions the stable host-side configuration for an Edutelligence
Pyris instance using the external-Weaviate Docker Compose topology.

## Ownership

Ansible owns `application.yml`, `llm_config.yml`, `docker.env`, users,
directories, certificate links, and the deployment helper. The deployment
workflow owns `runtime.env`, including `PYRIS_DOCKER_TAG`.

Rendering configuration does not restart an existing Pyris deployment. A fresh
host starts automatically when `pyris_bootstrap_runtime` is enabled (the
default) and the working directory did not exist before Ansible adoption.
Failed first boots retain a pending marker and retry on the next play. Existing
or legacy installations never auto-start merely because their checkout is
missing. Set `pyris_apply_runtime: true` only for an explicitly approved
restart of an existing deployment. Runtime commands are always skipped in
Ansible check mode.

Bootstrap state lives in `/var/lib/artemis-ansible/pyris` and the pending marker
is written before `/opt/pyris` is created. A provisioning failure at any later
task therefore remains retryable.

## Required variables

```yaml
pyris_general_config: {}
pyris_llm_config: []

proxy_ssl_certificate_path: /var/lib/rbg-cert/live/pyris.example/fullchain.pem
proxy_ssl_certificate_key_path: /var/lib/rbg-cert/live/pyris.example/privkey.pem
proxy_ssl_certificate_source_path: /var/lib/rbg-cert/live/host:f:pyris.example.fullchain.pem
proxy_ssl_certificate_key_source_path: /var/lib/rbg-cert/live/host:f:pyris.example.privkey.pem
```

For workflow deployments:

```yaml
pyris_create_deployment_user: true
pyris_deployment_user_public_keys:
  - ssh-ed25519 AAAA...
pyris_deployment_user_authorized_keys_exclusive: true
```

Secret-bearing configuration files are written with mode `0600`. Callers must
provide secrets through inventory variables backed by a secret manager; secret
values must not be committed.

The deployment helper retains the public contract:

```text
pyris-docker.sh restart <docker-tag> <git-branch>
```

For both first adoption and later deployments, `restart` clones and validates
the requested branch before stopping the current container. The mutable image
tag remains in `runtime.env`.
