Role Name
=========

This role creates a wireguard VPN between a group of servers. Each server in the host group can connecto to each other node.

Role Variables
--------------
See `defaults/main.yml` for the default values.

You have to define a host group from your inventroy which contains all the hosts that should be connected to each other:
```
wireguard_hostgroup: "{{ groups.<group_name_here> }}"
```
Each host in the host group has to specify the following `host_vars`:

```
# IPv6 address (with CIDR!) which can be used to access the node
wireguard_host_ipv6_address:  # (If left blank, Ansible will try to fill it with the hostfacts)
wireguard_interface_address: "fcfe:0:0:0:0:0:a:1" # Address of the node inside the network.
wireguard_pubkey:
wireguard_privkey:
```
## Automatic `host_var` generation

This role contains a python script to generate the `host_var` files. Make sure to install the wireguard tools first - The python script uses the `wg` command to generate the keys.

You have to configure the host prefix for your variables.

```
python3 host_var_gen.py --hostprefix artemis_ --hostsuffix .ase.in.tum.de
```
This will generate:
```
artemis_broker.ase.in.tum.de.yml
artemis_db.ase.in.tum.de.yml
artemis_node.ase.in.tum.de.yml
artemis_proxy.ase.in.tum.de.yml
artemis_storage.ase.in.tum.de.yml
```

You can specify the desired number of hosts with the script - Consult the script help for details:

```
python3 host_var_gen.py -h
```

## Manual Key generation

The wireguard keys can be genereated by hand with:
```
wg genkey | tee peer_A.priv | wg pubkey > peer_A.pub
```

