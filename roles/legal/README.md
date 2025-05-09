# Legal

This role manages the legal documents needed by Artemis.

## Configuration

To configure the role, you need to set the required variables in your Ansible playbook or inventory. The following variables are required:

- `artemis_legal_path`: The path where the legal documents will be stored. Default is `/opt/artemis/legal`.
- `artemis_user`: The user who will own the legal documents. Default is `artemis`.
- `artemis_group`: The group who will own the legal documents. Default is `artemis`.

## Example Usage

Here is an example playbook:

```yaml
- hosts: all
  roles:
    - role: ls1intum.legal
      vars:
        artemis_legal_path: "/opt/artemis/legal"
        artemis_user: "artemis"
        artemis_group: "artemis"
```
