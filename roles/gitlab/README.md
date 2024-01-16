Role Name
=========

This role installs GitLab inside a Docker container for the use with artemis.

Role Variables
--------------

Default variables can be found in the `defaults/main.yml` file.

You have to configure the following variables for this role:

```
gitlab_external_url: # External hostname under which GitLab will be accessible, including http(s)
gitlab_root_password: # The initial root password for the GitLab instance
```


An example playbook can be found in the `examples` folder.

A reverse proxy for GitLab should be installed for handling certificates, e.g. using the `ls1intum.artemis.proxy` role.