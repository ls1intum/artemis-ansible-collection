# Node storage setup role

This role adds an systemd service which automatically mounts the defined NFS export to /etc/storage. 

Variables that can be configured (See `defaults/main.yml`: 

```
artemis_uid: 1337
artemis_gid: 1337
artemis_user: artemis
artemis_group: artemis

storage_server_address: "fcfe:0:0:0:0:0:9:1" # This is the default address for the storage server in the wireguard network
storage_export:  /srv/artemis
```

If you change some of these variables, make sure to add them to you artemis `group_var`. These variables are shared between the `storage-client` and `storage-provider` role.

