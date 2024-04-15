Role Name
=========

This role installs Jenkins inside a Docker container for the use with artemis.

Role Variables
--------------

Default variables can be found in the `defaults/main.yml` file.

The initial password will be printed by the role.


An example playbook can be found in the `examples` folder.

A reverse proxy for Jenkins should be installed for handling certificates, e.g. using the `ls1intum.artemis.proxy` role.