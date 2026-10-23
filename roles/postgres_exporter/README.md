# PostgreSQL Exporter

This role sets up the [PostgreSQL exporter](https://github.com/prometheus-community/postgres_exporter)
for Prometheus. It creates the database role used for scraping and then hands the installation
over to `prometheus.prometheus.postgres_exporter`, the maintained successor of the archived
cloudalchemy roles.

It is the PostgreSQL counterpart of the `mysqld_exporter` role in this collection. Run it on the
database host, after the role that installs PostgreSQL.

## What it does

1. Creates the login role `postgres_exporter_db_user` and grants it `pg_monitor`, the read-only
   monitoring role PostgreSQL ships. That covers every collector without access to table data.
2. Optionally creates the `pg_stat_statements` extension in the scraped database.
3. Installs the exporter and its systemd unit, listening on `0.0.0.0:9187`.

## Configuration

Only the password is required:

```yaml
postgres_exporter_db_password: "your_exporter_password"
```

Everything else has a default in `defaults/main.yml`. The ones worth setting:

| Variable | Default | Notes |
| --- | --- | --- |
| `postgres_exporter_db_user` | `exporter` | Login role this role creates. |
| `postgres_exporter_db_password` | – | Required. |
| `postgres_exporter_db_name` | `postgres` | Database the exporter connects to. |
| `postgres_exporter_db_port` | `5432` | Used both for the exporter's connection and for Ansible's. |
| `postgres_exporter_release` | `0.20.1` | Exporter version. |
| `postgres_exporter_listen_address` | `0.0.0.0:9187` | |
| `postgres_exporter_collectors` | `[]` | Collectors to enable on top of the defaults. |
| `postgres_exporter_pg_stat_statements` | `false` | Create the extension in `postgres_exporter_db_name`. |

### Which database to scrape

Cluster-wide statistics - `pg_stat_database`, `pg_stat_bgwriter`, replication, locks - look the
same from any database, so the default of `postgres` is enough for host level monitoring. The
per-relation collectors and `pg_stat_statements` only ever see the database of the connection,
so set `postgres_exporter_db_name` to the Artemis database if you want table and query level
metrics:

```yaml
postgres_exporter_db_name: "{{ artemis_database_dbname }}"
postgres_exporter_collectors:
  - stat_statements
postgres_exporter_pg_stat_statements: true
```

`stat_statements` additionally needs `pg_stat_statements` in the server's
`shared_preload_libraries`, which is a server restart rather than something this role can do.

### Authentication

The exporter connects over TCP on the loopback address rather than over the unix socket,
because it runs as its own system user (`postgres-exp`) and peer authentication would try to
match that operating system user to a database role of the same name. So `pg_hba.conf` needs a
password entry for the loopback addresses:

```
host  all  all  127.0.0.1/32  scram-sha-256
host  all  all  ::1/128       scram-sha-256
```

Ansible itself connects as the `postgres` operating system user over the socket, the same way
`geerlingguy.postgresql` manages its own users, so no password is needed for that.

## Firewall

The exporter listens on 9187. The `firewall` role in this collection opens that port for
`monitoring_host_ipv4` / `monitoring_host_ipv6` in the `default` rule set.

## Example Usage

```yaml
- hosts: db
  roles:
    - role: geerlingguy.postgresql
      become: true

    - role: ls1intum.artemis.postgres_exporter
      become: true
      vars:
        postgres_exporter_db_password: "your_exporter_password"
        postgres_exporter_db_name: "artemis"
        postgres_exporter_db_port: 5432
```

## Dependencies

Install all with ```ansible-galaxy install -r meta/requirements.yml```
