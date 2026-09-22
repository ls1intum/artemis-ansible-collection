# Isolated Hyperion generation worker

Deploy the standalone Hyperion supervisor, not an Artemis server or LocalCI build
agent. This role requires a compatible Artemis core/worker release using explicit
toolchain identity (protocol 3). The shipped adapter supports Java/Gradle only.
The core role leaves whole-exercise generation disabled by default.

## Infrastructure prerequisites

Provision a **dedicated generation host or VM** with Docker and outbound access to
an approved image registry, model provider and dedicated TLS Apache Artemis
broker. The Docker socket grants the supervisor host-level authority; do not use
the Docker daemon of an Artemis core, database, repository server or build agent.
A test server may use a separate VM on the same physical machine, but must not
share that machine's Docker socket with core. The role's `dedicated_host` assertion
records the operator's decision; it cannot attest VM or network isolation.

This role does not provision the broker, certificates, firewall, Docker runtime
or VM. Use the matching Artemis release's `docker/hyperion/broker.xml` as the
broker authorization contract: private TLS CORE listener (61617), pre-created
per-worker command/event queues, separate core and per-worker accounts, and no
worker permissions to create/delete queues or manage the broker. The collection's
ordinary `broker` role is a browser messaging service with different permissions;
it is **not** an isolated Hyperion broker. Do not reuse its shared credentials.

Use a certificate trusted by the worker JVM and core JVM. For a private CA,
provision that CA in the pinned application images' JVM truststores before
publishing them. Do not disable hostname verification or enable `trustAll`.
Keep passwords out of broker URLs. Store credentials in Ansible Vault or the
inventory's existing secret-manager lookups, never in an image or git.

Enforce host-level egress restrictions: permit approved broker/model/registry
endpoints, deny database, repository/NFS, core management and cloud metadata
endpoints. This role does not install firewall rules; container egress must be
covered by the host's Docker-aware firewall. Generated-code sandboxes have no
network, credentials, host mounts or Docker socket. The supervisor publishes no
ports and runs read-only as UID 1000 with the dedicated socket's group.

## Example inventory and playbook

Install `community.docker` from the collection's `requirements.yml`. Provision
Docker first, then use a separate host group, for example `hyperion_staging`:

```yaml
# host_vars/generation.staging.example.yml
hyperion_worker_dedicated_host: true
hyperion_worker_id: staging-worker-1
# Replace these with qualified registry references containing 64 hex digest digits.
hyperion_worker_image: "registry.example/hyperion-worker@sha256:<digest>"
hyperion_worker_sandbox_image: "registry.example/hyperion-java-gradle@sha256:<digest>"
hyperion_worker_toolchain: java-gradle
hyperion_worker_slots: 1
hyperion_worker_broker_url: "tcp://generation-broker.staging.example:61617?sslEnabled=true&verifyHost=true&callTimeout=5000&callFailoverTimeout=5000"
hyperion_worker_broker_user: staging-worker-1
hyperion_worker_broker_password: "{{ vault_hyperion_worker_broker_password }}"
hyperion_worker_model_base_url: "https://approved-provider.example/v1"
hyperion_worker_model: qualified-model
hyperion_worker_model_api_key: "{{ vault_hyperion_worker_model_api_key }}"
```

```yaml
- name: Deploy isolated staging authoring workers
  hosts: hyperion_staging
  roles:
    - ls1intum.artemis.hyperion_worker
```

The provider must implement the OpenAI-compatible chat API. Use its documented
Spring AI base URL; the exact URL path depends on the provider. The model is bound
to `spring.ai.openai.chat.options.model`, with retries disabled for attributable
usage. Prompt/tool content capture is disabled. Provider access is worker-local:
the core's model configuration is not inherited.

Configure only eligible core nodes with LocalVC, LocalCI and a supported distributed
data provider (Hazelcast or Redis/Valkey with the provider-neutral coordination
implementation; older Artemis revisions that reject Redis are not compatible):

```yaml
artemis_hyperion_enabled: true
artemis_hyperion_exercise_generation_enabled: true
artemis_hyperion_workers:
  broker_url: "tcp://generation-broker.staging.example:61617?sslEnabled=true&verifyHost=true&callTimeout=5000&callFailoverTimeout=5000"
  user: staging-hyperion-core
  password: "{{ vault_hyperion_core_broker_password }}"
  ids: [staging-worker-1]
```

The worker itself has no Hazelcast/Redis, database, or repository credentials.
Only core/LocalVC writers participate in the application coordination store:

- With Hazelcast, use data-member writer nodes and configure the expected member
  count consistently; admission requires all members and recovery a strict majority.
- With Redis/Valkey, use the same authoritative, persistent, non-evicting store on
  every writer, with `valkey_appendonly: true`, `valkey_appendfsync: always`, and
  `valkey_maxmemory_policy: noeviction`. Define these in shared inventory variables
  for both the Valkey host and Artemis writer hosts; core admission validation
  rejects the snapshot-only defaults. Apply and verify them on the store before
  enabling generation. Permit `CLIENT LIST`: Artemis verifies unique process incarnations
  independently of human-readable client names and fails closed if the view is
  incomplete. There is no Hazelcast member-count requirement for Redis clients.
- Never flush/replace the coordination store under running writers. Asynchronous
  Redis failover can lose acknowledged writes; this role does not certify automatic
  failover safety. Drain and stop writers before store recovery, reconcile interrupted
  saves, and verify a canary before reopening authoring.
- A disconnected writer can still be writing Git or the database. Non-cancellable
  slots require the existing audited, exact-token recovery after the owning JVM is
  confirmed stopped; they are not released automatically on connection loss.

Core and worker accounts must differ. All writer nodes must run the compatible
exercise-mutation guard. Use distinct accounts, hosts, queues and model budgets
for staging, production and test servers. Do not add test workers to a production
core's ID list. No inventory is enabled automatically by installing this role.

## Capacity and maintenance

Defaults: one slot (range 1–16), 2 GiB and two CPU equivalents per generated-code
sandbox, 256 sandbox PIDs, plus a 2 GiB/two-CPU supervisor. Host memory must cover
all concurrent sandboxes, supervisor JVM, Docker and the OS; these are limits,
not a sizing guarantee. Start small and measure. The role preloads the digest-pinned
sandbox image; no job can request an image pull. `runtime` defaults to `runc`;
install and qualify an alternative such as `runsc` before selecting it.

The role refuses to touch an already-running supervisor unless
`hyperion_worker_maintenance_confirmed: true` is explicitly supplied. This is
conservative: even a normal rerun requires the maintenance check. Before setting
it, prevent new authoring requests and verify all runs, including saving phases,
have finished. The flag does not drain automatically. The worker has a two-minute
shutdown bound; Docker allows 150 seconds before forced termination. Neither is
a substitute for draining persistence on core.

Promote immutable worker and sandbox digests after qualification in staging.
Drain and upgrade core writers and workers together; do not mix protocol versions.
Back up database, repositories and deployment configuration, retain prior digests,
and coordinate rollback of both sides. The role does not wipe application data.

## Verification

Check **Administration → AI generations** for the exact worker identity, toolchain,
heartbeat and slot count. Ansible container startup is not application readiness.
Run one controlled unreleased Java/Gradle exercise through generation, verify
solution/starter grading and saved artifacts, cancel another run, and test undo.
In staging, test worker interruption, reconnect and guarded recovery before
production rollout. Confirm ordinary LocalCI builds remain independent.

Local role checks require no infrastructure credentials or model calls:

```sh
python -m unittest discover -s tests -p 'test_hyperion_worker.py' -v
ansible-lint roles/hyperion_worker
```

These tests validate configuration, secret quoting and container restrictions;
they do not certify TLS connectivity, host isolation or live generation.
