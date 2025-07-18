Redis
=========

This role installes Redis in a docker container and configures it for the use with artemis.

Please install docker before continuing with this role.

Role Variables
--------------

Default variables can be found in the `defaults/main.yml` file.

You have to configure the follwoing varaibles in your ansible `group_vars`:

```
redis:
  user: artemis # Also used by the artemis role
  password: #FIXME # Also used by the artemis role
```
