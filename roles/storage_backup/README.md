# Storage Backup

This role adds a cron job to the Storage host which creates regular Storage backups. The encryption keys will be saved to `./decryption_Keys.txt` on the localhost.

## Requirements
You need a borg server at `storage_backup_borg_server_url` with an ssh key set up. The borg server should be added to the known_hosts of the Artemis Storage host.

## Configuration

The default configuration will create a Storage backup every day at 4:30:

```yaml
storage_export: /srv/artemis

storage_backup_borg_server_user: borg
storage_backup_borg_server_user_home: /backup
storage_backup_borg_ssh_identity: /root/.ssh/id_borg
storage_backup_borg_server_port: 22
storage_backup_borg_repo_name: artemis-storage

storage_backup_script_path: /opt/backup.sh
storage_backup_compression: zstd
storage_backup_retention: 30
storage_backup_minute: 30
storage_backup_hour: 4
```

### Variables that have to be configured:

```yaml
storage_backup_borg_server_url: "your_borg_server_url"
storage_backup_password: "your_storage_backup_password"
```
Note that the password can be set to the empty string to store the backup without a password.

## Example Usage

Here is an example playbook:

```yaml
- hosts: storage
  roles:
    - role: ls1intum.artemis.storage_backup
      vars:
        storage_backup_password: "your_storage_backup_password"
```
