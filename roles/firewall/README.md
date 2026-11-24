# Firewall

This role is responsible for configuring the firewalls.

## Configuration

To configure the role, you need to set the required variables in your Ansible playbook or inventory. The following variables are required:

- `management_network_ipv4`: The IPv4 management network used to allow SSH / HTTP access to hosts and services.
- `management_network_ipv6`: The IPv6 management network used to allow SSH / HTTP access to hosts and services.
- `monitoring_host_ipv4`: The IPv4 address of the monitoring service.
- `monitoring_host_ipv6`: The IPv6 address of the monitoring service.
- `firewall_hostgroup`: The firewall rule set to be applied. Can be 'nodes', 'proxy' or left blank for default rules.

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
firewall_hostgroup:  # Can be 'nodes', 'proxy' or left blank for default rules
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

## Restricting the destinations of containers

The `nodes` rule set can limit where containers on the Docker bridge networks may connect to. Set the subnets Docker
assigns to its networks and the destinations that are off limits, per address family:

```yaml
firewall_container_subnets_ipv4: ["192.168.0.0/16"]
firewall_container_restricted_destinations_ipv4: ["10.0.0.0/24"]
```

```yaml
firewall_container_restricted_host_ports: [5701, 6379]
```

Traffic from a container to a service on the Docker host itself does not pass the `DOCKER-USER` chain, which only sees forwarded traffic, but the `INPUT` chain. A rule is therefore generated in `INPUT` for every
subnet and port in `firewall_container_restricted_host_ports`, so that a later rule that allows more cannot open these ports to containers. The default policy of `INPUT` already drops what is not allowed explicitly.

The rules match everything except packets of established and related connections, so replies of a restricted destination to a connection that it opened to a container are not dropped. They apply to the `nodes` host group and to Docker with the iptables backend. A destination that overlaps
a container subnet can also cut the traffic inside it, depending on whether the host filters bridged traffic. `firewall_container_restricted_host_ports` covers services that listen on the host. A port that a container publishes is reached over the forwarded path, and `DOCKER-USER` sees the address of the container and not the address of the host, so list the address or the subnet of the container that publishes it.
The rule files are validated with `iptables-restore --test` before they replace the loaded ones. When the IPv6 subnets are used, a change of the IPv6 rules restarts Docker, which reinstalls its IPv6 chains.

A rule is generated for every subnet and destination pair in the `DOCKER-USER` chain. Nothing is generated while one of the two
lists of a family is empty, which is the default. The rules do not apply to containers that use the network of the host,
and applying changed rules restarts Docker as described above, so roll them out one build agent at a time.

## Example Usage

Here is an example playbook for the Artemis nodes:

```yaml
- hosts: artemis
  roles:
    - role: ls1intum.artemis.firewall
      vars:
        firewall_hostgroup: nodes
```
