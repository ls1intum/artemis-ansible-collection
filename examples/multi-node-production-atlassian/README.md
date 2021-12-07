# Artemis multi node setup / artemis cluster setup

This is an example configuration for an artemis cluster consisting of three artemis nodes. In this example the cluster uses Jira, Bitbucket and Bamboo as external systems. 


# Setup 

Steps to uses this ansible configuration: 
- Copy the files of the desired example to your ansible configuration
- Update the host names in the inventory file
- Install the artemis ansible collection to your computer (Consult repository readme for details) 
- Install the collection dependencies (Again - consult the repository readme for details)
- Generate the necessary `host_vars` for the wireguard network - You can use the generation script in the [wireguard role](../../roles/wireguard/host_var_gen.py)
- Open the `group_vars/artemis_cluster.yml` file and fill the missing values and passwords ( e.g. resolve all `#FIXME`s)
- Check the playbooks for additional special variables which might need adjustment 
- Execute the `artemis-cluster-complete-setup.yml` playbook - It will call all the other playbooks in the correct order 



# Troubleshooting 
Here we gather some common problems: 
- The group var file for the cluster has to have the same name as the group in your inventroy file! 
- Configure only the external systems you need/have. Delete all blocks in the "External Systems Configuration" section in the group vars you don't need! 
