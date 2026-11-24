# Ansible Collection - ls1intum.artemis

This collection contains all ansible roles necessary to deploy [Artemis](https://github.com/ls1intum/Artemis).

> This is a work in progress repository - Please open issues if you encounter problems.

# Installation

## Artemis 10.8

Use Collection **2.6.0** for Artemis 10.8. It supports the
[LLM catalog and preset assignments](https://docs.artemis.tum.de/admin/llm-configuration/).
Collection 2.5.0 uses the earlier LLM settings. When upgrading an existing
installation to 10.8, migrate the LLM settings in your inventory before deploying.

Once 2.6.0 is published on Ansible Galaxy, install it with:

```sh
ansible-galaxy collection install ls1intum.artemis:2.6.0
```

Until then, install the compatible Collection directly from this Git commit:

```sh
ansible-galaxy collection install git+https://github.com/ls1intum/artemis-ansible-collection.git,05936935ddfef98b226e8138f54d84057b12dff5
```

The pinned Git commit still reports `2.5.0` in the installation output.
If replacing a previously installed Collection, add `--force` to the install
command. Then follow the [dependency installation steps](#install-dependencies).
For older Artemis releases, keep the Collection version compatible with that release.

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

## Isolated AI workers

The optional [`ai_worker` role](roles/ai_worker/README.md) deploys the
standalone authoring supervisor on a dedicated generation host or VM. It is not
an Artemis core profile or a LocalCI build agent. Generation remains disabled in
the core role unless explicitly enabled; existing inventories are unaffected.
Use the [separate test, staging and production inventories](examples/ai_worker/inventories)
and the [worker configuration guide](roles/ai_worker/README.md) to configure each environment.
Do not share provider state or credentials between environments.

# Deployment Strategies

Artemis can be deployed in different ways. Depending on the use case the ansible configuration differs.

## Single Node installation
All Artemis components are deployed to a single host. This is the prefered deployment strategy for small installations or testing/evaluation purposes.

## Multi Node installation (Cluster)
Artemis components are installed on different hosts. Currently the following components need to be set up for an Artemis cluster:

- Artemis application servers (1..n - Also referred to as "Artemis node")
- Reverse Proxy (1)
- Message Broker (1)
- Valkey (1)
- Shared Storage Provider (1)
- Database (1)

This setup allows to scale Artemis to support many concurrent users.

## Version Control & Continuous Integration

Artemis has a built-in version control and continuous integration system, the so-called Integrated Code Lifecycle.
Alternatively, you can use the built-in version control with an external continuous integration system.
The following external CI systems are supported:

- **Jenkins** - Traditional Jenkins integration
- **Hades** - External CI system via [hades](https://github.com/ls1intum/hades) and [hades-artemis-adapter](https://github.com/ls1intum/hades-artemis-adapter)

# Ansible Development Setup 

It is a good idea to install ansible and ansible-lint to a venv: 

```
virtualenv venv
. venv/bin/activate.fish
pip3 install -r requirements.txt
```

Run the build log storage template regression test locally without changing any hosts:

```bash
ansible-playbook -i localhost, tests/artemis-build-log-storage.yml
```
