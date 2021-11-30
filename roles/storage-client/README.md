# Node storage setup role

This role adds an systemd service which automatically mounts the defined NFS export to /etc/storage. 

Variables that have to be configured: 

```
artemis_user: user that is used to start artemis 
artemis_group: group of the artemis user

storage_address: IP address of the storage mount (e.g. 172.24.70.132)
storage_export: Share path on the storage server (e.g. /srv/artemis)
```
