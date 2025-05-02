# Jenkins

This role installs Jenkins inside a Docker container for the use with Artemis.

## Configuration

To configure the role, you need to set the required variables in your Ansible playbook or inventory. The following variables are required:

- `jenkins_internal_port`: The internal port for Jenkins.
- `jenkins_data_dir`: The data directory for Jenkins.
- `jenkins_docker_tag`: The Docker tag for Jenkins.

Default variables can be found in the `defaults/main.yml` file.

### Variables that have to be configured:

```
jenkins_internal_port: 8082
jenkins_data_dir: "/opt/jenkins/data"
jenkins_docker_tag: "lts"
```

## Example Usage

Here is an example playbook:

```yaml
- hosts: jenkins
  roles:
    - role: ls1intum.jenkins
      vars:
        jenkins_internal_port: 8082
        jenkins_data_dir: "/opt/jenkins/data"
        jenkins_docker_tag: "lts"
```

The initial password will be printed by the role.

A reverse proxy for Jenkins should be installed for handling certificates, e.g. using the `ls1intum.artemis.proxy` role.
