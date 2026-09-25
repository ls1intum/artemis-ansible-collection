# AI Worker node

Deploy the normal Artemis WAR as a **worker-only node**. The worker image runs
`ArtemisApp` with `prod,aiworker`. It has no HTTP listener, database access or
repository credentials. It connects to the same Artemis `DistributedDataProvider`
as core: as a Hazelcast client discovered through Eureka, or as a Redis/Valkey
client. No Artemis message broker or worker-specific queues are required.

Use a dedicated VM or host. The supervisor's Docker socket grants host-level
control. Do not share the core, database or Build Agent Docker daemon. This role
does not install Docker, the provider, Eureka or firewall rules. Allow outbound
access only to the selected provider, the approved model endpoint, the image
registry and approved telemetry. Generated-code containers have no network.

## Example: Hazelcast

```yaml
# Dedicated worker inventory; supply secrets through Ansible Vault.
ai_worker_dedicated_host: true
ai_worker_id: generation-1
ai_worker_image: "registry.example/artemis-aiworker@sha256:<64 hex digits>"
ai_worker_sandbox_image: "registry.example/hyperion-sandbox@sha256:<64 hex digits>"
ai_worker_workload: hyperion-generation
ai_worker_profile: java-gradle
ai_worker_provider: hazelcast
ai_worker_eureka_url: "https://admin:{{ vault_registry_password }}@registry.example/eureka/"
ai_worker_model_base_url: "https://approved-model.example/v1"
ai_worker_model: qualified-model
ai_worker_model_api_key: "{{ vault_ai_worker_model_api_key }}"
```

The worker uses `spring.hazelcast.localInstances=false`, so its Hazelcast client
joins the same named cluster as production core nodes. Eureka must advertise
core members on addresses the worker host can reach. The worker does not
register itself as a Eureka service or become a Hazelcast data member.

## Example: Redis/Valkey

Replace the provider settings above with:

```yaml
ai_worker_provider: redis
ai_worker_valkey:
  host: valkey.internal
  port: 6379
  username: generation-worker
  password: "{{ vault_generation_worker_valkey_password }}"
```

Use the same authoritative Redis/Valkey deployment and distributed-data
namespace as core. Give the worker a separate restricted account if your
provider policy supports it. The worker must read and write its command,
event, heartbeat and lease data. Eureka is disabled for this provider.

## Core and writer settings

On every eligible core coordinator, use the collection's `artemis` role with:

```yaml
artemis_hyperion_enabled: true
artemis_hyperion_exercise_generation_enabled: true
artemis_aiworker_ids: [generation-1]
# Set artemis_aiworker_enabled: true only for worker coordination without Hyperion generation.
```

Keep `artemis_hyperion_exercise_generation_enabled: true` on every exercise
writer, even a writer that does not run Hyperion. This enables the mutation
guard on those nodes. A generation coordinator also needs `core`, `localci`
and `localvc` profiles. The core and worker must use the same provider.

```yaml
- name: Deploy isolated generation workers
  hosts: generation_workers
  roles:
    - ls1intum.artemis.ai_worker
```

Pin both images by SHA-256 digest. Set `ai_worker_maintenance_confirmed: true`
only after new work is stopped and active assignments and core persistence have
drained. The role checks for a running worker before replacement, protects the
rendered configuration, preloads the sandbox image and starts the worker with
no published ports. The model key stays on the worker; generation model calls
go from the worker directly to the model provider, not through core.

After deployment, check worker capacity in Artemis Administration and run a
small generation, cancellation and undo test. A green container status alone
does not prove the provider or sandbox is ready.
