Role Name
=========

This role is responsible to configure the firewalls

Role Variables
--------------

Default variables can be found in the `defaults/main.yml` file.

You have to configure the follwoing varaibles:

```
# Management Networks - used to allow SSH / HTTP access to Hosts and services
management_network_ipv4: "172.24.152.0/24"
management_network_ipv6: "2a09:80c0:ac18:9800::/64"

# Monitoring Service
monitoring_host_ipv4: "131.159.89.160"
monitoring_host_ipv6: "2a09:80c0:89:1::32"
```

You have to configure a special varaible to select the firewall rule set which is applied:

```
firewall_hostgroup:  # Can be 'broker', 'nodes', 'proxy' or left blank for default rules
```

## Example usage:

Example playbook for a broker:

```
    - role: ls1intum.artemis.firewall
      tags: firewall
      vars:
        firewall_hostgroup: broker
```
