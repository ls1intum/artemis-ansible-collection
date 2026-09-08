Valkey
=========

This role installs Valkey from the distribution's package repository and
configures it for use with Artemis (distributed cache, locks, websocket pub/sub
and the LocalCI build queue).

Valkey is a fork of Redis 7.2 and speaks the same protocol, so nothing changes on
the Artemis side: the Spring properties and environment variables are still
`spring.data.redis` / `SPRING_DATA_REDIS_*`, and the build queue data store is
still called `Redis` in the Artemis configuration. Only the server and this
role's variables changed - see "Migrating from the redis role" below.

Requirements
------------

A Debian or Ubuntu host with `valkey-server` and `valkey-tools` in its package
sources:

| Distribution     | Valkey version | Source                               |
| ---------------- | -------------- | ------------------------------------ |
| Ubuntu 24.04 LTS | 7.2            | universe                             |
| Ubuntu 25.04     | 8.0            | universe                             |
| Debian 13        | 8.x            | main                                 |
| Debian 12        | 8.0            | bookworm-backports (enable it first) |

The role installs whatever the enabled repositories offer; it does not add one.
If you need a newer Valkey than your distribution ships, add the repository you
trust (for example Percona's) with your usual repository management and set
`valkey_packages` accordingly - everything else in this role works unchanged, the
configuration uses no directive newer than Valkey 7.2.

Network exposure
----------------

Valkey listens on `127.0.0.1` and on this host's WireGuard address only. That
binding plus the `firewall` role's "wg0 and lo only" `INPUT` policy are the
network boundary; the ACL users below are the privilege boundary.

The WireGuard address is bound without the optional `-` prefix on purpose: if
`wg0` is not up, `valkey-server` exits and systemd retries until the interface
exists. The alternative would be a Valkey that starts fine and is silently
unreachable for every Artemis node.

That deliberate failure mode needs one adjustment to the packaged unit, which
this role installs as a drop-in (`/etc/systemd/system/valkey-server.service.d/`):
the unit has `Restart=always`, but systemd's default start rate limit gives up
after five restarts within ten seconds and leaves the unit failed - with nothing
to bring it back once `wg0` appears. The drop-in disables the rate limit, sets a
`RestartSec` backoff, orders the unit after `wg-quick@wg0.service`, and raises
`LimitNOFILE` to `valkey_nofile_limit`.

Users
-----

Three ACL users are configured:

| User                    | Purpose             | Privileges                                                                                       |
| ----------------------- | ------------------- | ------------------------------------------------------------------------------------------------ |
| `default`               | -                   | disabled (`off nopass nocommands`)                                                                 |
| `valkey.username`       | Artemis application | all keys and channels, `+@all -@admin -@dangerous` plus the read-only extras Lettuce/Redisson need on connect (`INFO`, `CONFIG GET`, `SORT_RO`, `CLIENT SETNAME/SETINFO/GETNAME/ID/INFO`) |
| `valkey.admin_username` | operations          | `+@all`                                                                                            |

The `default` user is disabled but still carries a password. That is not
redundant: `protected-mode` rejects every non-loopback connection while the
default user has the `nopass` flag - independently of `bind`, and independently
of the other users being password-protected. With `nopass` the Artemis nodes get

```
DENIED Redis is running in protected mode because protected mode is enabled
and no password is set for the default user.
```

Giving the user a password clears the flag, while `off` still rejects every
`AUTH` as that user - verified including an attempt with the correct password,
from a non-loopback address. The password is a SHA-256 digest derived from the
admin password, so it is deterministic across Ansible runs, never appears in
plaintext, and is nothing anyone can look up. Protected mode therefore stays on
as a fail-safe for the case where this ACL block is lost or mangled.

**Valkey has no source-address ACL.** A user cannot be restricted to localhost or
to the WireGuard network - that distinction only exists at the network layer, via
`bind` and the firewall. The two users are a *privilege* boundary: a leaked
Artemis credential (it sits in `application-prod.yml` on the nodes) cannot run
`FLUSHALL`, `CONFIG SET`, `SHUTDOWN`, `DEBUG`, `KEYS`, `REPLICAOF` or `ACL`, so
the blast radius of a compromised node is bounded. Keep the admin password out of
the Artemis inventory group so it never reaches the nodes.

Of the commands in the `admin` and `dangerous` categories, exactly six are
reachable for the Artemis user: `INFO`, `CONFIG GET`, `SORT_RO`, `ROLE`,
`MODULE LIST` and `CLIENT LIST`. Everything else in those categories - `FLUSHALL`,
`CONFIG SET`, `SHUTDOWN`, `KEYS`, `DEBUG`, `MONITOR`, `REPLICAOF`, `ACL`,
`CLIENT KILL/PAUSE` - is denied.

If Artemis hits a denied command it shows up in `ACL LOG`, which is the fastest
way to find the whole set at once instead of one redeploy per `NOPERM`:

```bash
valkey-cli --user admin --askpass acl log 25
```

Check a candidate change without restarting anything:

```bash
valkey-cli --user admin --askpass acl dryrun artemis client list
```

Widen `valkey_artemis_acl_rules` rather than falling back to `+@all`.

Role Variables
--------------

Default variables can be found in the `defaults/main.yml` file.

Ansible replaces dictionaries wholesale, so anything you do not list under
`valkey:` in your `group_vars` loses its default. Only the keys the `artemis` role
also reads live in that dict; every operational setting is a flat `valkey_*`
variable.

You have to configure the following in your ansible `group_vars`:

```yaml
valkey:
  username: artemis     # Also used by the artemis role
  password: #FIXME      # Also used by the artemis role
  admin_username: admin
  admin_password: #FIXME
  port: 6379            # Also used by the artemis role
```

The Artemis nodes reach Valkey over WireGuard, so set `valkey.host` there to the
Valkey host's WireGuard address (unbracketed - Spring adds the brackets itself).

Configuration file
------------------

The role templates the whole of `/etc/valkey/valkey.conf`; `valkey-server` reads
exactly one file and does not merge in the packaged defaults, so an overlay is
not an option. Two consequences:

* On a package upgrade dpkg sees a modified conffile and keeps this version, so a
  Valkey update never silently drops the ACL block. It also means new upstream
  defaults are not picked up - review `/etc/valkey/valkey.conf.dpkg-dist` after a
  major version upgrade.
* `CONFIG SET` changes are lost on the next Ansible run or restart. Change the
  variable, not the running server.

Sizing for a large cluster
--------------------------

The defaults are sized conservatively; review these for a multi-node deployment:

```yaml
valkey_maxmemory: 4gb       # ~60-70% of the RAM available to Valkey
valkey_maxclients: 10000    # Redisson keeps large per-node pools
valkey_nofile_limit: 65535  # must stay above valkey_maxclients
```

`maxmemory-policy` is `noeviction` on purpose. Redisson locks, the LocalCI build
queue and the websocket bookkeeping are not disposable cache entries - evicting
them corrupts cluster coordination without any error. Reaching the limit should
be a loud write failure, so alert on `used_memory` from `INFO memory`.

There is no cgroup memory limit on the service: `maxmemory` is the cap, and a
`MemoryMax` below the peak RSS (dataset plus the copy-on-write pages a `BGSAVE`
fork dirties) would have the kernel kill Valkey mid-snapshot instead. Leave the
host enough headroom above `maxmemory` for that fork.

`stop-writes-on-bgsave-error` is `no`: with the Valkey default, one failed
snapshot (full disk, wrong permissions) puts every write into `MISCONF` and takes
the whole Artemis cluster down until an operator intervenes. Alert on
`rdb_last_bgsave_status` from `INFO persistence` instead.

Host tuning
-----------

`valkey_tune_host` (default `true`) sets `vm.overcommit_memory=1` (required for
reliable `BGSAVE` forks) and `net.core.somaxconn`.

Transparent huge pages are handled in the configuration: `disable-thp yes` makes
Valkey turn them off for its own process at startup, which is what causes the
latency spikes during background saves. Disabling them host-wide (for example via
`transparent_hugepage=never` on the kernel command line) is still the more
thorough option and is not managed by this role.

Migrating from the redis role
-----------------------------

This role replaces the `redis` role, which ran `redis:7.4-alpine` in Docker with
`network_mode: host`. The security model, the ACL users and the tuning are
unchanged; the packaging is not.

1. **Rename the variables.** `redis:` becomes `valkey:` with the same keys, and
   every flat `redis_*` variable becomes `valkey_*`. The `artemis` role reads
   `valkey.host`, `valkey.port`, `valkey.username` and `valkey.password` now, so
   rename it in the Artemis groups too, and `artemis_redis_client_name` becomes
   `artemis_valkey_client_name`. Both roles fail with an explicit message if
   `redis` is still defined. The Spring property and environment variable names
   (`spring.data.redis`, `SPRING_DATA_REDIS_*`) and the LocalCI `data-store:
   "Redis"` value stay as they are - those name Spring's client and Artemis'
   enum, not the server.

2. **Do not migrate the RDB file.** Valkey 7.2 refuses to load a snapshot written
   by Redis 7.4 (newer RDB version), and everything in there is coordination
   state - Redisson locks, the build queue, websocket bookkeeping - that is
   rebuilt on startup. Plan a maintenance window with the Artemis nodes down and
   start with an empty dataset. Queued builds are lost; drain them first if that
   matters.

3. **Remove the old deployment** once Valkey is up:

   ```bash
   docker compose -f /opt/redis/docker-compose.yml down
   rm -rf /opt/redis
   ```

   The data directory moves from `/opt/redis/redis-data` to `/var/lib/valkey`,
   owned by the `valkey` system user the package creates (no fixed UID, unlike
   the container's 999).

4. **Ports and firewall are unchanged** - still 6379 on loopback and wg0. Docker
   is no longer involved on this host for Valkey, which also removes the reason
   the old role insisted on host networking: Docker's published-port DNAT rules
   bypassing the firewall's `INPUT` chain.
