# Firewall

This role is responsible for configuring the firewalls.

## Configuration

To configure the role, you need to set the required variables in your Ansible playbook or inventory. The following variables are required:

- `management_network_ipv4`: The IPv4 management network used to allow SSH / HTTP access to hosts and services.
- `management_network_ipv6`: The IPv6 management network used to allow SSH / HTTP access to hosts and services.
- `monitoring_host_ipv4`: The IPv4 address of the monitoring service.
- `monitoring_host_ipv6`: The IPv6 address of the monitoring service.
- `firewall_hostgroup`: The firewall rule set to be applied. Can be 'registry', 'nodes', 'proxy' or left blank for default rules.

Default variables can be found in the `defaults/main.yml` file.

### Variables that have to be configured:

```
# Management Networks - used to allow SSH / HTTP access to Hosts and services
management_network_ipv4: "172.24.152.0/24"
management_network_ipv6: "2a09:80c0:ac18:9800::/64"

# Monitoring Service
monitoring_host_ipv4: "131.159.89.160"
monitoring_host_ipv6: "2a09:80c0:89:1::32"
```

You have to configure a special variable to select the firewall rule set which is applied:

```
firewall_hostgroup:  # Can be 'registry', 'nodes', 'proxy' or left blank for default rules
```

## Interaction with Docker

The rule sets in `templates/` define the whole `*filter` and `*nat` tables, so loading them with
`iptables-restore` also removes the chains Docker installs when the daemon starts (`DOCKER`,
`DOCKER-USER`, `DOCKER-FORWARD`, ...) together with the `MASQUERADE` rule for the bridge network.
Docker does not notice this and only reinstalls the rules on restart, so containers lose all
outbound connectivity in the meantime.

To avoid that, this role only reloads the rules when they actually changed, and afterwards checks
whether Docker's `MASQUERADE` rule is still present. If it is missing, Docker is restarted so it
can reinstall its rules. Note that this restart stops running containers, which on a build agent
means losing the builds that are currently in flight.

## Example Usage

Here is an example playbook for a registry:

```yaml
- hosts: registry
  roles:
    - role: ls1intum.artemis.firewall
      vars:
        firewall_hostgroup: registry
```
