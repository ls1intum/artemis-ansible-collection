# Storage Client

This role adds a systemd service which automatically mounts the defined NFS export to /mnt/storage.

## Configuration

To configure the role, you need to set the required variables in your Ansible playbook or inventory. The following variables are required:

- `artemis_uid`: The UID for the Artemis user.
- `artemis_gid`: The GID for the Artemis group.
- `artemis_user`: The name of the Artemis user.
- `artemis_group`: The name of the Artemis group.
- `storage_server_address`: The address of the storage server.
- `storage_export`: The path to the NFS export on the storage server.

Default variables can be found in the `defaults/main.yml` file.

### Variables that have to be configured:

```
artemis_uid: 1337
artemis_gid: 1337
artemis_user: artemis
artemis_group: artemis

storage_server_address: "fcfe:0:0:0:0:0:9:1" # This is the default address for the storage server in the wireguard network
storage_export: /srv/artemis
```

## Example Usage

Here is an example playbook:

```yaml
- hosts: storage_client
  roles:
    - role: ls1intum.storage_client
      vars:
        artemis_uid: 1337
        artemis_gid: 1337
        artemis_user: artemis
        artemis_group: artemis
        storage_server_address: "fcfe:0:0:0:0:0:9:1"
        storage_export: "/srv/artemis"
```
