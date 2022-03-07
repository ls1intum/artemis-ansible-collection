MySQLd Exporter
=========

Role to setup the [MySQLd exporter](https://github.com/prometheus/mysqld_exporter) for prometheus.
It creates a user on the MySQL database on the host, which is needed for scraping the data.


Role Variables
--------------

Default variables can be found in the `defaults/main.yml` file.

Important: Change database user password!

Dependencies
--------------
Install all with ```ansible-galaxy install -r meta/requirements.yml´´´
