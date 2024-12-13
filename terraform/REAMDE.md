### README

## Terraform Configuration for GCP

This project provisions a custom network, firewall rules, and a VM instance on Google Cloud using Terraform.

### Requirements

1. **GCP Account**:
   - Enable the Compute Engine API.
   - Create a service account with `Compute Admin` and `Compute Network Admin` roles.
   - Authenticate with:
     ```bash
     gcloud auth application-default login
     ```

2. **Terraform**:
   - Install from [Terraform Installation Guide](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli).


### Resources

1. **Network**: Custom network `default-network`.
2. **Firewall**: Allows traffic for:
   - SSH (22), HTTP (80), HTTPS (443).
   - Source range: `35.235.240.0/20`.
3. **VM Instance**: `e2-micro` with Debian 11 and startup script.