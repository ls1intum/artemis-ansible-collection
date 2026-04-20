# Migration Tester

This role is for a VM to test out database migrations. If it breaks something, the database can be reset to a previous point by a docker recreate, without needing to sql import the database again.

## Configuration

To configure the role, you need to set the required variables in your Ansible playbook or inventory. The following variables are required:

- `artemis_database_password`: The Artemis Database password

When adding a new database image, additionally this will have to be added:
- `dump_src`: The local path of the db backup, as .sql.gz file
- `bake: true`

Running without bake, the database image will be recreated and therefore be reset to the last bake run.
