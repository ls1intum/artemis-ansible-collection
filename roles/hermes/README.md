# Hermes

This role deploys [Hermes](https://github.com/ls1intum/Hermes), the push notification relay service for Artemis, via Docker Compose. Hermes forwards push notifications to iOS devices via Apple Push Notification Service (APNs) and to Android devices via Firebase Cloud Messaging (FCM).

## Description

This role sets up a Hermes deployment that includes:

- **Hermes**: Push notification relay service for Artemis
- **APNs Integration**: Apple Push Notification Service support for iOS devices
- **FCM Integration**: Firebase Cloud Messaging support for Android devices

## Prerequisites

Before using this role, ensure the following requirements are met:

### System Requirements

- **Operating System**: Ubuntu 20.04+ or Debian 11+
- **Docker Engine**: 20.10 or later
- **Docker Compose**: v2.0 or later

### Docker Installation

This role **does not** install Docker. You must install Docker and Docker Compose before running this role. You can:

1. Use a Docker installation role from Ansible Galaxy
2. Install manually: https://docs.docker.com/engine/install/
3. Use your organization's preferred Docker installation method

### Certificates

You need to obtain the following credentials before deploying:

- **Apple APNs Certificate**: A `.p12` certificate for sending push notifications to iOS devices
- **Google Firebase Credentials**: A service account JSON file for sending push notifications to Android devices

## Configuration

To configure the role, you need to set the required variables in your Ansible playbook or inventory.

### Required Variables

The following variables **must** be set:

```yaml
# Hermes Docker image version
hermes_version: "1.0.0"

# Working directory for Hermes deployment
hermes_working_directory: "/opt/hermes"

# Port to expose Hermes on (maps to container port 8080)
hermes_port: "8080"

# Apple Push Notification Service (APNs) configuration
hermes_apns_certificate_path: "artemis-apns.p12"
hermes_apns_certificate_password: "your-certificate-password"
hermes_apns_certificate_content: "base64-encoded-p12-certificate"
hermes_apns_prod_environment: true

# Google Firebase Cloud Messaging configuration
hermes_google_application_credentials_json_path: "firebase.json"
hermes_google_application_credentials_content: |
  {
    "type": "service_account",
    ...
  }
```

### Variable Reference

| Variable | Description |
|---|---|
| `hermes_version` | Docker image tag for `ghcr.io/ls1intum/hermes` |
| `hermes_working_directory` | Directory where Docker Compose and certificates are stored |
| `hermes_port` | Host port mapped to Hermes container port 8080 |
| `hermes_apns_certificate_path` | Filename for the APNs `.p12` certificate on disk |
| `hermes_apns_certificate_password` | Password for the APNs `.p12` certificate |
| `hermes_apns_certificate_content` | Base64-encoded content of the APNs `.p12` certificate |
| `hermes_apns_prod_environment` | Set to `true` for production APNs, `false` for sandbox |
| `hermes_google_application_credentials_json_path` | Filename for the Firebase credentials JSON on disk |
| `hermes_google_application_credentials_content` | Content of the Firebase service account JSON file |

## Example Usage

### Basic Installation

```yaml
- hosts: hermes
  roles:
    - role: ls1intum.artemis.hermes
      vars:
        hermes_version: "1.0.0"
        hermes_working_directory: "/opt/hermes"
        hermes_port: "8080"
        hermes_apns_certificate_path: "artemis-apns.p12"
        hermes_apns_certificate_password: "{{ vault_apns_password }}"
        hermes_apns_certificate_content: "{{ vault_apns_certificate_b64 }}"
        hermes_apns_prod_environment: true
        hermes_google_application_credentials_json_path: "firebase.json"
        hermes_google_application_credentials_content: "{{ vault_firebase_credentials }}"
```

### Artemis Integration

To connect Artemis to this Hermes instance, set the following variable in your Artemis role configuration:

```yaml
push_notification_relay: "https://hermes.example.com"
```

## Post-Installation

### Verify Installation

After running the role, verify the installation:

1. **Check service status**:

   ```bash
   cd /opt/hermes
   docker compose ps
   ```

2. **View logs**:

   ```bash
   cd /opt/hermes
   docker compose logs -f hermes
   ```

## Security Considerations

- Store all secrets (APNs certificate password, certificate content, Firebase credentials) in **Ansible Vault**
- The APNs certificate and Firebase credentials files are created with `0600` permissions (root-only access)
- The `docker-compose.yml` is created with `0600` permissions to protect environment variables
- Certificate volumes are mounted as read-only (`:ro`) in the container

## Files and Directories

After deployment, the following structure exists:

```
/opt/hermes/                     # (or custom hermes_working_directory)
├── docker-compose.yml           # Docker Compose configuration
├── artemis-apns.p12             # APNs certificate
└── firebase.json                # Firebase credentials
```

## Related Documentation

- [Hermes Repository](https://github.com/ls1intum/Hermes)
- [Artemis Documentation](https://docs.artemis.tum.de/)
