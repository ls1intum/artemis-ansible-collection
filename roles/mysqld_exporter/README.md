# MySQLd Exporter

This role sets up the [MySQLd exporter](https://github.com/prometheus/mysqld_exporter) for Prometheus. It creates a user on the MySQL database on the host, which is needed for scraping the data.

## Configuration

To configure the role, you need to set the required variables in your Ansible playbook or inventory. The following variables are required:

- `mysql_exporter_user`: The username for the MySQL exporter.
- `mysql_exporter_password`: The password for the MySQL exporter.
- `mysql_exporter_version`: The version of the MySQL exporter.
- `mysql_exporter_dsn`: The Data Source Name (DSN) for the MySQL exporter.

Default variables can be found in the `defaults/main.yml` file.

### Variables that have to be configured:

```
mysql_exporter_user: "exporter"
mysql_exporter_password: "your_exporter_password"
mysql_exporter_version: "0.14.0"
mysql_exporter_dsn: "{{ mysql_exporter_user }}:{{ mysql_exporter_password }}@(localhost:3306)/"
```

Important: Change the database user password!

## Example Usage

Here is an example playbook:

```yaml
- hosts: db
  roles:
    - role: ls1intum.mysqld_exporter
      vars:
        mysql_exporter_user: "exporter"
        mysql_exporter_password: "your_exporter_password"
        mysql_exporter_version: "0.14.0"
        mysql_exporter_dsn: "exporter:your_exporter_password@(localhost:3306)/"
```

## Dependencies

Install all with ```ansible-galaxy install -r meta/requirements.yml```
