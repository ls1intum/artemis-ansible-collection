Role Name
=========

This role creates an NFS export which is used by the artemis nodes to share data (repositories/uploads etc.)

By default the wireguard interfaces are used for NFS. This ensures encrypted traffic and client authorization. 


Role Variables
--------------
See `defaults/main.yml`. 

If you change some of these variables, make sure to add them to you artemis `group_var`. These variables are shared between the `storage-client` and `storage-provider` role.

