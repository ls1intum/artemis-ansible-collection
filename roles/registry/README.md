# Registry

This role installs the jhipster registry and configures it for the use with artemis.

## Configuration

To configure the role, you need to set the required variables in your Ansible playbook or inventory. The following variables are required:

- `artemis_jhipster_jwt`: The JWT secret for Artemis.
- `artemis_jhipster_registry_password`: The password for the JHipster registry.

Default variables can be found in the `defaults/main.yml` file.

### Variables that have to be configured:

```
artemis_jhipster_jwt: "your_jwt_secret"
artemis_jhipster_registry_password: "your_registry_password"
```

The Token can be generated with: `openssl rand -base64 64`. Consult the artemis role readme for details.

## Example Usage

Here is an example playbook:

```yaml
- hosts: registry
  roles:
    - role: ls1intum.registry
      vars:
        artemis_jhipster_jwt: "your_jwt_secret"
        artemis_jhipster_registry_password: "your_registry_password"
```
