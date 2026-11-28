# First university installation

This inventory runs Artemis 10.8 on two Ubuntu Server 26.04 LTS VMs. One VM runs the native Artemis core, LocalVC, PostgreSQL 18 and Valkey. The other runs the native LocalCI build agent and executes student builds in Docker. The core uses its embedded WebSocket broker. A single core keeps Git repositories, uploads and build logs on local durable storage. This deployment has a single point of failure.

## Prepare the hosts

- Provide SSH access with sudo and Python 3 on both VMs. Enable the standard Ubuntu repositories, including universe. Reserve UID and GID 1337 for the Artemis service. Start with one build slot. Size RAM and disk for the exercises, repository growth and PostgreSQL. Each VM should have at least 8 GiB for this example. A course running larger builds will need more worker memory.
- Put the VMs on a private routed network or VPN. Bind Valkey to the core's private IP. Allow its TCP port 6379 from the worker host only. PostgreSQL uses loopback. Limit management SSH to administrators. Block build containers from the private infrastructure and management networks at the worker's forwarding firewall, including traffic to the worker host itself. Allow the worker service to reach the core over HTTPS and Valkey. Allow registry and package downloads needed by your exercises.
- Provide a public DNS name and an HTTPS ingress with a trusted certificate and renewal. Route the hostname to port 8080 on the core and allow that port only from the ingress. Preserve the Host header, set X-Forwarded-Proto to https, replace client-supplied forwarding headers, and support WebSocket upgrades, Git-over-HTTPS pushes and uploads. Both VMs must resolve and trust the public URL. The core role waits for its public `/management/info` endpoint during deployment.
- Back up the PostgreSQL database, Valkey persistence, the Artemis working directory and the encrypted inventory to off-host storage. The base playbook provisions the application and its dependencies. Configure and rehearse recovery before enrolling students. The [restore rehearsal](../../roles/db_backup/restore-rehearsal.md) covers those roles and the Valkey snapshot for this topology.

For an existing nginx ingress, the following site serves HTTP and WebSocket traffic through the same upstream. Replace the hostname, certificate paths and private address. If nginx runs on the core, use `127.0.0.1:8080` as the upstream.

```nginx
map $http_upgrade $artemis_connection {
    default upgrade;
    ''      close;
}
server {
    listen 443 ssl;
    server_name artemis.example.edu;
    ssl_certificate /etc/ssl/artemis/fullchain.pem;
    ssl_certificate_key /etc/ssl/artemis/privkey.pem;
    client_max_body_size 100m;
    location / {
        proxy_pass http://192.0.2.10:8080;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $remote_addr;
        proxy_set_header X-Forwarded-Proto https;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $artemis_connection;
        proxy_request_buffering off;
        proxy_read_timeout 900s;
    }
}
```

## Configure the inventory

From the root of a private deployment repository, add the collection as a Git submodule and copy its example. Choose a revision containing this example. Record the submodule commit in the deployment repository so future installations and recovery use the same application and backup roles.

```bash
git submodule add https://github.com/ls1intum/artemis-ansible-collection.git vendor/artemis-ansible-collection
# For an unreleased example, check out its reviewed revision in the submodule first.
cp -R vendor/artemis-ansible-collection/examples/university/. .
```

Edit the addresses in `hosts.yml` and `group_vars/all.yml`, the HTTPS URL, support address and login label. Set the real organization, administrator and university names in `group_vars/core.yml`. Artemis shows them on its About page. By default this example uses local accounts, turns off telemetry and leaves exercise sharing unconfigured.

Create an encrypted variables file on the controller. The following commands assume Python 3.13 or later and Git.

```bash
python3 -m venv .venv
. .venv/bin/activate
python -m pip install 'ansible==14.3.0'
ansible-galaxy collection install ./vendor/artemis-ansible-collection -p ./collections --force
export ANSIBLE_COLLECTIONS_PATH="$PWD/collections"
ansible-vault create secrets.yml
```

Give the vault five independent values. Generate each password with `openssl rand -hex 32` and the JWT signing secret with `openssl rand -base64 64 | tr -d '\n'`. Preserve the JWT and passwords across runs. Keep the vault passphrase outside the repository.

```yaml
vault_artemis_admin_password: "<generated password>"
vault_artemis_database_password: "<generated password>"
vault_artemis_jwt: "<base64-encoded 64 random bytes>"
vault_valkey_password: "<generated application password>"
vault_valkey_admin_password: "<different generated administrative password>"
```

## Deploy and verify

```bash
ansible-inventory -i hosts.yml --graph
ansible-playbook -i hosts.yml deploy.yml --syntax-check
ansible-playbook -i hosts.yml deploy.yml -e @secrets.yml --ask-vault-pass
```

On a fresh controller, run `git submodule update --init` before installing the collection. Use the same submodule revision when provisioning the backup roles. The play installs Valkey on the core and Docker on the worker. Both hosts get OpenJDK 25, the release WAR and an enabled systemd unit. The worker uses per-job HTTPS clone tokens. Only the Valkey application credential is needed on both hosts.

1. Fetch `https://<your-host>/management/health/readiness` and check for `UP`. On each VM check `systemctl is-active artemis`. The first start creates the schema and initializes application services. If the first login times out after readiness turns green, check `journalctl -u artemis -b` and `/opt/artemis/artemis.log` for startup progress, then retry.
2. Sign in as `artemis_admin` with the vault password. In Server Administration, check that the build agent is online with one build slot. Create a programming exercise in a trial course, submit a change and verify that its build result and feedback arrive.
3. Configure the university's SMTP and identity provider, if required, before distributing accounts. Plan upgrades separately from first installation. This play stops and restarts both services and downloads the selected WAR each time.

The collection's [Artemis role](../../roles/artemis/README.md) documents authentication and optional modules. The [10.8 release](https://github.com/ls1intum/Artemis/releases/tag/10.8) includes the WAR and its checksums.

### Verification record

On 28 November 2026, this example ran on two fresh Ubuntu 26.04 arm64 VMs with Artemis 10.8, PostgreSQL 18, Valkey 9.1.2 and the native deployment roles at collection commit `f3145b8`. The test ingress used a local CA. Private SSH forwards connected the two isolated VM networks for HTTPS and Valkey. The HTTPS readiness probe returned `UP`, and the administrator saw one build worker with one slot. A C/FACT submission produced automatic result 3 for commit `172a3d0082cf6faeb449f4e43eb9b1ba38666524`, with all three tests passing and a score of 100%.
