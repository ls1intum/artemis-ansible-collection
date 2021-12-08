# Ansible Collection - ls1intum.artemis

This collection contains all ansible roles necessary to deploy [Artemis](https://github.com/ls1intum/Artemis).

> This is a work in progress repository - Please open issues if you encounter problems.

# Installation
## Installation via ansible-galaxy:

Not possible yet - We're working on it!

## Installation via git:

### Manual install:

```
ansible-galaxy collection install git+https://github.com/ls1intum/artemis-ansible-collection.git,main
```

### Install via requirements file:

Add the following to your ansible requirements:
```
collections:
  - name: https://github.com/ls1intum/artemis-ansible-collection.git
    type: git
    version: main # You can also specify a spcific version here!
```

## Install dependencies

[Ansible does not support role dependencies for collections](https://github.com/ansible/ansible/issues/76030) - So you need to install the dependencies by hand :(.

The repository contains a `requirements.yml` file which contains all the external roles used in artemis. Please install these with ansible galaxy:

```bash
#This command will only work if you installed the collections to the default location!

ansible-galaxy install -r ~/.ansible/collections/ansible_collections/ls1intum/artemis/requirements.yml
```

# Documentation

You can find the documentation for Artemis [here](https://docs.artemis.ase.in.tum.de).
Each role includes a readme and default configuration. Consult these for more information.

 **Use the examples in the examples folder as starting point for your deployment**

# Deployment Strategies

Artemis can be deployed in different ways. Depending on the use case the ansible configuration differs.

You can find examples for each configuration in the `examples` folder.

## Single Node installation
All Artemis components are deployed to a single host. This is the prefered deployment strategy for small installations or testing/evaluation purposes.

## Multi Node installation (Cluster)
Artemis components are installed on different hosts. Currently the following components need to be set up for an Artemis cluster:

- Artemis application servers (1..n - Also referred to as "Artemis node")
- Reverse Proxy (1)
- Message Broker (1)
- JHipster registry (1)
- Shared Storage Provider (1)
- Database (1)

This setup allows to scale Artemis to support many concurrent users.

## External Services

Artemis relies on external services to handle version control and continuous integration. Currently two configurations are supported by Artemis:
- Jira, Bitbucket, Bamboo
- Gitlab, Jenkins

The ansible configuration has to be adapted accordingly. Again, you can find examples for both in the `examples` folder.

## Test Servers

This collection also allows to provision test servers/clusters. To provision a test server or test cluster, set the

```
is_testserver: true
```
variable in your `group_vars`.

## Tests

All roles have been tested on ubuntu 20.04 LTS
