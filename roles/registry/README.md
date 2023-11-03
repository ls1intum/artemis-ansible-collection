Role Name
=========

This role installs the jhipster registry and configures it for the use with artemis.

Role Variables
--------------

Default variables can be found in the `defaults/main.yml` file.

You have to configure the follwoing varaibles in your ansible `group_vars`:

```
artemis_jhipster_jwt: #(Also used by the Artemis role)
artemis_jhipster_registry_password: # (Also used by the Artemis role)
```

The Token can be generated with: `openssl rand -base64 64`. Consult the artemis role readme for details.
