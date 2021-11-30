# Ansible Configuratioin 
Independent of the deployment strategy, we recommend the usage of `host_vars` and `group_vars`. Many variables are shared between roles. Hence, it is a good idea to specifiy them only once. 

In single node installation this is not as important, but for multi-node installations group_vars are vital. Some configuration have to be set for each hosts. We will discuss all important variables here. The readme files of the individual roles might provide more information for specific edge-cases. 

# Host Groups
We suggest to specifiy host groups for each compoent in your inventroy. Namely: 
```

[artemis_nodes]
node[1:3].artemis.ase.in.tum.de

[artemis_db]
db1.artemis.ase.in.tum.de

[artemis_broker]
broker1.artemis.ase.in.tum.de

[artemis_proxy]
proxy.artemis.ase.in.tum.de

[artemis_storage]
storage.artemis.ase.in.tum.de

[artemis:children]
artemisnodes
artemisdb
artemisbroker
artemisproxy
artemis_storage
 
```
For each group you should add a `group_var` file.

# Variables 
## Common Group Vars (independent of external services)
TODO
- `artemis`: Here all the shared configurations should be placed. 
    - `artemis_user_name:`: Linux User on all the Hosts to execute services
    - `artemis_user_group`: Linux Group for the artemis user
    - `artemis_database_host`: Specify the database host 
    - `artemis_database_username`: Spefify the artemis database user 
    - `artemis_database_password` Password for the artemis database user
    - `artemis_database_dbname` Artemis Database name
- `artemis_nodes`: 
    - `artemis_version`: Artemis version that should be installed 
    - `artemis_internal_admin_user`: Artemis admin user 
    - `artemis_internal_admin_password`: Artemis admin user password
    - ``
- `artemis_db`:
- `artemis_broker`:
- `artemis_proxy`: 

## Host Vars 
- Each node must specify 
    - `wireguard_ipv6_address`: IP address used for the VPN tunnle
    - `wireguard_interface_address: "fcfe:0:0:0:0:0:a:1"` IP address inside the tunnle
    - `wireguard_pubkey` Both can be generated with `wg genkey | tee peer_A.key | wg pubkey > peer_A.pub`
    - `wireguard_privkey`

- Artemis Nodes: Each node must specify 
    - a unique `node_id`

## Variables for External Services 
TODO

### Atlassian 
TODO

### Gitlab Jenkins 
TODO

### LDAP
TODO

### Mail 
