# AI Worker

Deploy the current Artemis generation worker, not a broker service or a LocalCI
Build Agent. Core and worker must be built from the same qualified Artemis WAR.
The worker image starts `prod,aiworker`. These Spring profiles apply in **all**
environments; do not replace `prod` with Spring's `test` profile.

The supported Hyperion capability is `hyperion-generation`, version `1`, with
profile `java-gradle`. A different version or toolchain fails validation.
Generation stays disabled in the core role by default.

## Test, staging and production

Use one [inventory](../../examples/ai_worker/inventories) per environment. The
examples use separate hosts, provider endpoints, worker IDs, model endpoints,
models and capacity. They contain no credentials or usable image digests.
Production generation is disabled until an operator enables it.

1. Copy the selected inventory into your deployment repository. Replace every
   `example.invalid` address. Copy [deploy.yml](../../examples/ai_worker/deploy.yml)
   into your deployment repository as `ai-worker.yml`. Add these groups and variables to your normal core
   inventory; the examples are not a complete Artemis installation.
2. Supply `ai_worker_release_image` and `ai_worker_release_sandbox_image` as full
   registry image references pinned by `@sha256:`. See
   [release.example.yml](../../examples/ai_worker/release.example.yml).
3. Store `vault_valkey_password` and `vault_ai_worker_model_api_key` in a separate
   encrypted Vault file for that environment. Never reuse production keys in test.
4. Apply the core variables with your existing Artemis playbook on **every**
   exercise-writing node. A writer needs the generation guard, not model access:
   `artemis_hyperion_exercise_generation_enabled: true` and
   `artemis_hyperion_enabled: false` are valid on a writer-only node. For bare-metal
   updates, set `update_artemis_config: true` and `restart_artemis: true` after
   draining authoring. An eligible
   `core,localci,localvc` coordinator also needs Hyperion and the worker IDs.
5. Deploy the worker on a dedicated Docker host or VM. Do not use the Docker
   daemon of core, a database, or an ordinary Build Agent. A separate local daemon
   is supported only with `ai_worker_isolated_daemon: true` and a non-default
   `ai_worker_docker_socket`.

Until the role is released, install a reviewed collection commit, not `main` or
an older published version. Set `COLLECTION_COMMIT` to that commit. `--force`
replaces an installed copy with the same collection version.

```sh
ansible-galaxy collection install \
  "git+https://github.com/ls1intum/artemis-ansible-collection.git,${COLLECTION_COMMIT:?set a reviewed collection commit}" --force
```

For example, with that collection installed:

```sh
# Use staging or prod in place of test. Select exactly one environment.
ansible-playbook -i inventories/test/hosts.yml ai-worker.yml \
  -e @release.yml -e @inventories/test/vault.yml --vault-id test@prompt \
  --tags validation

# After validation, deploy. No services are started by the validation-only run.
ansible-playbook -i inventories/test/hosts.yml ai-worker.yml \
  -e @release.yml -e @inventories/test/vault.yml --vault-id test@prompt
```

The host needs Docker and Python `requests` for the Ansible Docker modules.
The role does not provision Docker, VMs, provider services, networks or firewalls.
Use a private provider network (for example WireGuard); do not expose Redis or
the Docker API to the public network. Permit supervisor traffic only to its
provider, approved model endpoint and image registry. The generated-code containers have no network and receive no model key.
The supervisor has no published HTTP port. Its Docker socket grants host control.

Before replacing a running worker, stop new authoring and drain active assignments
and core persistence. Then set `ai_worker_maintenance_confirmed: true` for that
run. Do not set it permanently in inventory. A coordinated core/worker update is
required when the distributed-data encoding changes; do not mix runtime versions.

## Configuration

| Variables | Effect |
| --- | --- |
| `artemis_hyperion_agent` | Native `artemis.hyperion.agent` settings on core: token/duration budgets and named effort profiles. Core sends the resolved profile to the worker. |
| `artemis_hyperion_generation` | Native `artemis.hyperion.generation` settings on core: concurrency, retention and shutdown settings. |
| `artemis_generation_provider_max_retries` | SDK retry count on generation coordinators; default `0` at both common and chat levels for exact usage accounting. Nonzero values make usage incomplete. This also affects other model calls on that core. |
| `artemis_hazelcast_expected_data_member_count` | Actual number of Hazelcast data members. Required for multi-node Hazelcast authoring; the YAML and Docker paths set the same count. |
| `artemis_aiworker_ids` | Worker IDs admitted by each coordinator. Match the IDs on worker hosts. |
| `ai_worker_model_base_url`, `ai_worker_model`, `ai_worker_model_api_key`, `ai_worker_model_timeout` | Worker-local model connection. Use HTTPS. Set `ai_worker_microsoft_foundry` for a Foundry custom domain. |
| `ai_worker_model_options` | Allowed defaults: `temperature`, `top-p`, `max-tokens`, `max-completion-tokens`, and `reasoning-effort`. Connection settings and retries cannot be overridden here. An explicit core effort profile governs the run's model/options. |
| `ai_worker_slots`, `ai_worker_memory`, `ai_worker_cpus` | Supervisor capacity and container limits. |
| `ai_worker_sandbox_memory_bytes`, `ai_worker_sandbox_cpu_quota`, `ai_worker_sandbox_pids`, `ai_worker_runtime` | Per-sandbox limits. The host needs room for the supervisor, concurrent sandboxes and the OS. Example limits are not load-test results. |

The worker uses the current [Spring AI OpenAI properties](https://docs.spring.io/spring-ai/reference/api/chat/openai-chat.html):
`spring.ai.openai.chat.model`, rather than relying on the legacy `chat.options.model` alias. For an
OpenAI-compatible endpoint, include `/v1` in the base URL when its API requires
that prefix; the SDK appends `/chat/completions`. Use the provider root for
Foundry with `ai_worker_microsoft_foundry: true`.

The core role renders the same nested agent/generation settings in its YAML and
Docker paths. Docker uses `SPRING_APPLICATION_JSON` to preserve profile names;
do not override that variable separately. Set the model in each core effort
profile to a deployment available through that environment's worker endpoint.
Prices are operator-supplied: the examples use `artemis_llm_cost: {}` so stale
collection price defaults are not presented as measured generation costs.

## Provider isolation

Use `ai_worker_provider: redis` with `ai_worker_valkey` containing the same
`host`, `port`, `username` and `password` as core. The examples share the `valkey`
map within one inventory. The authoritative store must use AOF,
`appendfsync always`, and `maxmemory-policy noeviction`. Inventory validation is
not a check of the live server's effective settings.

For Hazelcast, set `ai_worker_provider: hazelcast` and
`ai_worker_eureka_url: "https://admin:{{ vault_registry_password }}@registry.example/eureka/"`.
On the core inventory, use the collection's multi-node Hazelcast/Eureka setup
(`is_multinode_install: true`) and set `artemis_hazelcast_expected_data_member_count`
to the actual data-member count on every member. All data members must use the
same count and the same exercise-generation flag before authoring starts. An intentional single core
with a remote worker uses a count of `1`; workers and Build Agents do not count.
A missing count fails validation before deployment. The worker is a fetch-only
Eureka/Hazelcast client, not a data member. Core
members must advertise addresses reachable from the worker.

**Do not share an authoritative provider across environments.** Worker IDs alone
do not isolate all distributed maps and topics. Use separate Redis/Valkey stores,
or separate Eureka/Hazelcast deployments and networks. All three environments
use the runtime's production cluster mode; an inventory name is not a namespace.

## Verification

Run the configuration playbook and Python tests in the PR's CI. They test both
provider modes and all three inventories without contacting their services.
After a real role deployment and explicit generation opt-in on core and all
writers, check capacity from core and generate a small exercise,
confirm solution/template LocalCI scores of 100/0, cancel another run, and undo a
saved run. Check the effective provider durability settings. Template tests and a
running container do not establish this live acceptance.
