# Storage Backup

This role adds a cron job to the Storage host which creates regular Storage backups.

## Configuration

The default configuration will create a Storage backup every day at 4:30:

```yml
storage_export: /srv/artemis
storage_backup_dir: /opt/backup

storage_backup_script_path: /opt/backup.sh
storage_backup_compression: zstd
storage_backup_retention: 30
storage_backup_minute: 30
storage_backup_hour: 4
```

### Variables that have to be configured:

```
storage_backup_password: "your_storage_backup_password"
```
Note that the password can be set to the empty string to store the backup without a password.

## Example Usage

Here is an example playbook:

```yaml
- hosts: storage
  roles:
    - role: ls1intum.storage_backup
      vars:
        storage_export: /srv/artemis
        storage_backup_password: "your_storage_backup_password"
        storage_backup_dir: /opt/backup

        storage_backup_script_path: /opt/backup.sh
        storage_backup_compression: zstd
        storage_backup_retention: 30
        storage_backup_minute: 30
        storage_backup_hour: 4
```
