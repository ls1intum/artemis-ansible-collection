# Rehearse an Artemis restore before the first course

Use a disposable installation with the university's planned Artemis configuration and a synthetic course. Record the Artemis version, PostgreSQL major version, database name and owner, the application data mounts, and the UID/GID used by Artemis. Allocate fresh database and storage destinations for a second installation. Isolate it from production DNS, SSO, SMTP, object stores, workers, and external integrations. Use internal test accounts and a build agent dedicated to the rehearsal.

## Create a recovery point

1. From an Artemis checkout containing the [trial grading check](https://github.com/ls1intum/Artemis/tree/develop/supporting_scripts/trial), run `node supporting_scripts/trial/verify-grading.mjs` against the disposable installation. A remote test listener can be reached through a loopback SSH tunnel. Set the port and the internal test administrator credentials as described in the trial guide. Keep the exercise ID and passing commit hash. Add a small course attachment and save its checksum if the installation stores uploaded files.
2. Drain builds and stop the **rehearsal** application's writers, including workers, before taking both backups. Keep PostgreSQL and storage available. Independently scheduled database and file backups can capture different points in time. Include every configured repository, upload and file-storage path. Back up the deployment inventory, keys and configuration separately. The database dump contains no cluster-wide roles.
3. Run the installed database backup script with `-d` and the storage backup script with `-s`. Set distinct paths such as `/opt/backup-database.sh` and `/opt/backup-storage.sh` if the roles share a host. Record the resulting dump filename and Borg archive name together. Retain a protected copy of this pair outside the installation, along with access to the Borg repository, passphrase and recovery key. Restart the source rehearsal installation only after both backups finish.

## Restore into empty destinations

Provision the recovery hosts with the same application and database versions. Keep Artemis stopped. Use the source database owner and the matching PostgreSQL client tools. Set `PGHOST`, `PGUSER`, `RESTORE_DB`, `ARTEMIS_DB_OWNER` and `DUMP` in a shell connected to the **rehearsal database server**. Supply credentials using the deployment's normal secret store. Pre-create the original database roles and use the source database encoding and locale.

```bash
set -euo pipefail
gzip -t "$DUMP"
createdb --template=template0 --owner="$ARTEMIS_DB_OWNER" "$RESTORE_DB"
gzip -dc "$DUMP" | psql -X --set=ON_ERROR_STOP=1 --single-transaction --dbname="$RESTORE_DB"
```

The database role produces a plain SQL dump compressed with gzip. Set the recovered Artemis datasource to this database.

On the recovery storage host, set `BORG_REPO` to the backup repository URL and `ARCHIVE` to the recorded archive. Use Borg 1.x, the same SSH identity and the corresponding passphrase supplied securely. Extract as a user able to restore the ownership and permissions.

```bash
set -euo pipefail
borg info "$BORG_REPO::$ARCHIVE"
restore_tree=$(mktemp -d)
(cd "$restore_tree" && borg extract --numeric-ids "$BORG_REPO::$ARCHIVE")
```

Borg stores the source directory inside the archive. For example, a backup of `/srv/artemis` extracts beneath `$restore_tree/srv/artemis`. Mount or copy **its contents** into the empty recovery data directory, preserving ownership and permissions. Check that the Artemis service account can read and write its repositories and uploads. Reconnect any additional restored mounts before starting the application and its dedicated worker.

## Prove the course can be taught again

1. Sign in to the recovered instance, open the original course and exercise, and verify the existing grade. If you saved an attachment, download it and compare its checksum.
2. Point the trial grading check at the **recovered** loopback listener. Run `node supporting_scripts/trial/verify-grading.mjs --exercise-id "$EXERCISE_ID"` with the original exercise ID. The check must obtain a fresh passing grade on the restored repository.
3. Record the backup pair, recovered exercise ID, previous and new commit hashes, elapsed recovery time, and any manual fixes. Repeat after changing the backup layout or upgrading PostgreSQL. Protect the rehearsal and its backups according to the university's retention policy.
