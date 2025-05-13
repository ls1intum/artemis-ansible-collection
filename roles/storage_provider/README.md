# Storage Provider

This role creates an NFS export which is used by the artemis nodes to share data (repositories/uploads etc.). By default, the wireguard interfaces are used for NFS. This ensures encrypted traffic and client authorization.

## Configuration

To configure the role, you need to set the required variables in your Ansible playbook or inventory. The following variables are required:

- `artemis_uid`: The UID for the Artemis user.
- `artemis_gid`: The GID for the Artemis group.
- `artemis_user`: The name of the Artemis user.
- `artemis_group`: The name of the Artemis group.
- `storage_export`: The path to the NFS export.
- `storage_network`: The network address for the storage.
- `storage_server_address`: The address of the storage server.

Default variables can be found in the `defaults/main.yml` file.

### Variables that have to be configured:

```
artemis_uid: 1337
artemis_gid: 1337
artemis_user: artemis
artemis_group: artemis

storage_export: /srv/artemis
storage_network: "fcfe:0:0:0:0:0:0:0/96"
storage_server_address: "fcfe:0:0:0:0:0:9:1"
```

## Example Usage

Here is an example playbook:

```yaml
- hosts: storage_provider
  roles:
    - role: ls1intum.storage_provider
      vars:
        artemis_uid: 1337
        artemis_gid: 1337
        artemis_user: artemis
        artemis_group: artemis
        storage_export: "/srv/artemis"
        storage_network: "fcfe:0:0:0:0:0:0:0/96"
        storage_server_address: "fcfe:0:0:0:0:0:9:1"
```
