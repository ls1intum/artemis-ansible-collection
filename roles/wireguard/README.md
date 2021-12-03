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
wireguard_host_ipv6_address: # IPv6 address (with CIDR!) which can be used to access the node 
wireguard_interface_address: "fcfe:0:0:0:0:0:a:1" # Address of the node inside the network. 
wireguard_pubkey: 
wireguard_privkey: 
```

The wireguard keys can be genereated with: 
```
wg genkey | tee peer_A.priv | wg pubkey > peer_A.pub
```

