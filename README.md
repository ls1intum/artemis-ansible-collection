# Ansible Collection - ls1intum.artemis

This collection contains all ansible roles necessary to deploy [Artemis](https://github.com/ls1intum/Artemis).

> This is a work in progress repository - Please open issues if you encounter problems.

# Installation
## Installation via [ansible-galaxy](https://galaxy.ansible.com/ls1intum/artemis):

```
ansible-galaxy collection install ls1intum.artemis
```

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

You can find the documentation for Artemis [here](https://docs.artemis.cit.tum.de).
Each role includes a readme and default configuration. Consult these for more information.

Our Ansible configuration for the TUM Artemis Production, Staging and Test environments are public at [github.com/ls1intum/artemis-ansible](https://github.com/ls1intum/artemis-ansible).
Use them as examples for how to use this collection and as a reference for deploying Artemis.

# Deployment Strategies

Artemis can be deployed in different ways. Depending on the use case the ansible configuration differs.

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

## Version Control & Continuous Integration

Artemis has a built-in version control and continuous integration system, the so-called Integrated Code Lifecycle.
Alternatively, you can use the built-in version control and Jenkins as an external continuous integration system.

# Ansible Development Setup 

It is a good idea to install ansible and ansible-lint to a venv: 

```
virtualenv venv
. venv/bin/activate.fish
pip3 install -r requirements.txt
```
