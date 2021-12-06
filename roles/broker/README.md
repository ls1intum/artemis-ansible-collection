Role Name
=========

This role installes activemq and the jhipster registry and configures both for the use with artemis. 

Role Variables
--------------

Default variables can be found in the `defaults/main.yml` file. 

You have to configure the follwoing varaibles in your ansible `group_vars`: 

```
broker: 
  url: # Broker hostname (Only used in the Artemis role)
  username: # Broker username (Also used by the Artemis role)
  password: # Broker password (Also used by the Artemis role)
```

and 

```
artemis_jhipster_jwt: #(Also used by the Artemis role)
artemis_jhipster_registry_password: # (Also used by the Artemis role)
```

The Token can be generated with: `openssl rand -base64 64`. Consult the artemis role readme for details.
