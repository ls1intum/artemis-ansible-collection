Redis
=========

This role runs Redis in a Docker container and configures it for use with Artemis
(distributed cache, locks, websocket pub/sub and the LocalCI build queue).

Please install Docker before continuing with this role.

Network exposure
----------------

Redis listens on `127.0.0.1` and on this host's WireGuard address only, and the
container runs with `network_mode: host`.

Host networking is deliberate. Docker's port publishing installs its own DNAT and
FORWARD rules, which are evaluated *before* the `INPUT` chain that the `firewall`
role manages - a published `6379:6379` is therefore reachable from every
interface, including the public one, regardless of the firewall rules. On the host
network both the `bind` directive and the firewall's "wg0 and lo only" `INPUT`
policy apply.

The WireGuard address is bound without the optional `-` prefix on purpose: if
`wg0` is not up, the container fails to start and Docker's restart policy retries
until it is. The alternative would be a Redis that starts fine and is silently
unreachable for every Artemis node.

Users
-----

Three ACL users are configured:

| User                   | Purpose                | Privileges                                                                                       |
| ---------------------- | ---------------------- | ------------------------------------------------------------------------------------------------ |
| `default`              | -                      | disabled (`off nopass nocommands`)                                                                 |
| `redis.username`       | Artemis application    | all keys and channels, `+@all -@admin -@dangerous` plus `INFO` and the `CLIENT` subcommands Lettuce/Redisson need |
| `redis.admin_username` | operations             | `+@all`                                                                                            |

**Redis has no source-address ACL.** A user cannot be restricted to localhost or
to the WireGuard network - that distinction only exists at the network layer, via
`bind` and the firewall. The two users are a *privilege* boundary: a leaked
Artemis credential (it sits in `application-prod.yml` on the nodes) cannot run
`FLUSHALL`, `CONFIG SET`, `SHUTDOWN`, `DEBUG`, `KEYS`, `REPLICAOF` or `ACL`, so
the blast radius of a compromised node is bounded. Keep the admin password out of
the Artemis inventory group so it never reaches the nodes.

If Artemis hits a denied command, it shows up in `ACL LOG`:

```bash
redis-cli --user admin --askpass acl log 10
```

Widen `redis_artemis_acl_rules` rather than falling back to `+@all`.

Role Variables
--------------

Default variables can be found in the `defaults/main.yml` file.

Ansible replaces dictionaries wholesale, so anything you do not list under
`redis:` in your `group_vars` loses its default. Only the keys the `artemis` role
also reads live in that dict; every operational setting is a flat `redis_*`
variable.

You have to configure the following in your ansible `group_vars`:

```yaml
redis:
  username: artemis     # Also used by the artemis role
  password: #FIXME      # Also used by the artemis role
  admin_username: admin
  admin_password: #FIXME
  port: 6379            # Also used by the artemis role
```

The Artemis nodes reach Redis over WireGuard, so set `redis.host` there to the
Redis host's WireGuard address (unbracketed - Spring adds the brackets itself).

Sizing for a large cluster
--------------------------

The defaults are sized conservatively; review these for a multi-node deployment:

```yaml
redis_maxmemory: 4gb              # ~60-70% of the RAM available to Redis
redis_container_memory_limit: 6g  # above maxmemory, leaving room for fork/COW
redis_maxclients: 10000           # Redisson keeps large per-node pools
redis_nofile_limit: 65535         # must stay above redis_maxclients
```

`maxmemory-policy` is `noeviction` on purpose. Redisson locks, the LocalCI build
queue and the websocket bookkeeping are not disposable cache entries - evicting
them corrupts cluster coordination without any error. Reaching the limit should
be a loud write failure, so alert on `used_memory` from `INFO memory`.

`stop-writes-on-bgsave-error` is `no`: with the Redis default, one failed
snapshot (full disk, wrong permissions) puts every write into `MISCONF` and takes
the whole Artemis cluster down until an operator intervenes. Alert on
`rdb_last_bgsave_status` from `INFO persistence` instead.

Migrating from the previous version of this role
------------------------------------------------

This role used to deploy `redis/redis-stack-server:6.2.6-v18`. It now deploys the
official `redis` image, because Artemis uses no redis-stack module and Redis 6.2
is end of life. `redis.version` is rejected with an error - use `redis_image`.

Before rolling this out:

1. Check what you are actually running today. The old role overrode the
   redis-stack entrypoint's command, so it is worth confirming which config file
   was in effect and whether any module was loaded:

   ```bash
   docker exec redis redis-cli -u redis://user:pass@127.0.0.1:6379 module list
   docker exec redis redis-cli -u redis://user:pass@127.0.0.1:6379 config get requirepass maxmemory
   ```

   If `module list` is non-empty, do not switch the image before checking what
   uses those modules.

2. The old compose file published `6379` on all interfaces and set
   `bind 0.0.0.0`. Assume the port was reachable from outside the WireGuard
   network and rotate `redis.password`.

3. This is a restart of the cluster's coordination layer - schedule a
   maintenance window. The data directory moves from a relative bind mount to
   `redis_data_directory` and is chowned to UID 999; existing RDB files from 6.2
   are read by 7.4 without conversion.

Host tuning
-----------

`redis_tune_host` (default `true`) sets `vm.overcommit_memory=1` (required for
reliable `BGSAVE` forks) and `net.core.somaxconn`.

Transparent huge pages are *not* handled by this role. They cause latency spikes
during background saves; disable them on the Redis host, for example via
`transparent_hugepage=never` on the kernel command line.
