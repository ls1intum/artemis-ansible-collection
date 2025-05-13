# DB Backup

This role adds a cron job to the db host which creates regular DB backups.

## Configuration

The default configuration will create a DB backup every day at 4:30:

```yml
artemis_database_dbname: artemis
artemis_database_backup_dir: /opt/backup
artemis_database_backup_script_path: /opt/backup.sh

artemis_database_backup_minute: 30
artemis_database_backup_hour: 4
```

## Example Usage

Here is an example playbook:

```yaml
- hosts: db
  roles:
    - role: ls1intum.db_backup
      vars:
        artemis_database_dbname: "artemis"
        artemis_database_backup_dir: "/opt/backup"
        artemis_database_backup_script_path: "/opt/backup.sh"
        artemis_database_backup_minute: 30
        artemis_database_backup_hour: 4
```
