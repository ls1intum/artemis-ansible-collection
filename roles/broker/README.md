Role Name
=========

This role installes activemq and configures it for the use with artemis.

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