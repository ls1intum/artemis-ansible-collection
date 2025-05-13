# Broker

This role installs ActiveMQ and configures it for use with Artemis.

## Configuration

To configure the role, you need to set the required variables in your Ansible playbook or inventory. The following variables are required:

- `broker.url`: The hostname of the broker.
- `broker.username`: The username for the broker.
- `broker.password`: The password for the broker.

Default variables can be found in the `defaults/main.yml` file.

### Variables that have to be configured:

```
broker:
  url: "broker.example.com" # Broker hostname (Only used in the Artemis role)
  username: "brokeruser" # Broker username (Also used by the Artemis role)
  password: "your_broker_password" # Broker password (Also used by the Artemis role)
```

## Example Usage

Here is an example playbook:

```yaml
- hosts: broker
  roles:
    - role: ls1intum.broker
      vars:
        broker:
          url: "broker.example.com"
          username: "brokeruser"
          password: "your_broker_password"
```
