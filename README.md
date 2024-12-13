# Discord ChatGPT README
## Overview

This project includes:
1. A **Discord bot** powered by OpenAI's GPT models to generate intelligent chat responses.
2. A **Terraform configuration** to provision Google Cloud Platform (GCP) resources for deployment.



## Features

### Discord Bot
- Uses OpenAI's API for natural language processing.
- Configurable prompts for system and user inputs.
- Dynamic message filtering based on sender attributes.

### Terraform Configuration
- Provisions GCP resources:
  - Custom network.
  - Firewall rules.
  - Compute Engine instance with startup script.



## Prerequisites

- **Discord Bot**:
  - A valid Discord bot token.
  - An OpenAI API key.
  - Python 3.8 or higher.
  - Docker (optional for containerized deployment).
- **Terraform**:
  - Installed from [Terraform Installation Guide](https://developer.hashicorp.com/terraform/tutorials/aws-get-started/install-cli).
  - A GCP project with enabled Compute Engine API.



## Discord Bot Setup

### Virtual Environment Setup

1. **Create**:
   ```bash
   python -m venv venv
   ```

2. **Activate**:
   - **Windows**: `venv\Scripts\activate`
   - **macOS/Linux**: `source venv/bin/activate`

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set Up Environment Variables**:
   - Create a `.env` file in the project directory:
     ```bash
     DISCORD_BOT_TOKEN=your_bot_token
     OPENAI_API_KEY=your_openai_api_key
     SYSTEM_PROMPT=
     MSG_PROMPT=
     OPENAI_MODEL=gpt-4
     MAX_RESPONSE_CHARS=2000
     ALLOW_BOTS=true
     NAME_PATTERN=.*
     TEMPERATURE=1
     MAX_TOKENS=2048
     TOP_P=1
     FREQUENCY_PENALTY=0
     PRESENCE_PENALTY=0
     ```

5. **Run the Bot**:
   ```bash
   python app.py
   ```

### Docker Setup

1. **Build the Docker Image**:
   ```bash
   docker build -t your-bot-name .
   ```

2. **Run the Docker Container**:
   ```bash
   docker run --env-file .env your-bot-name
   # or
   docker run -d --restart on-failure:3 --env-file .env your-bot-name
   ```



## Terraform Setup

1. **Clone the Repository**:
   ```bash
   git clone <repository_url>
   cd ./terraform
   ```

2. **Set Up Variables**:
   - Create a `terraform.tfvars` file:
     ```hcl
     project_id = "your-gcp-project-id"
     ```

3. **Initialize Terraform**:
   ```bash
   terraform init
   ```

4. **Plan the Infrastructure**:
   ```bash
   terraform plan
   ```

5. **Apply the Configuration**:
   ```bash
   terraform apply
   ```
   Confirm the changes when prompted.

6. **Clean Up Resources**:
   ```bash
   terraform destroy
   ```



## Resources Provisioned via Terraform

- **Google Compute Network**: 
  - Creates a custom network named `default-network`.

- **Firewall Rules**:
  - Allows ingress traffic for SSH (22), HTTP (80), and HTTPS (443).
  - Restricts source ranges to `35.235.240.0/20`.

- **Compute Engine Instance**:
  - Provisions a `e2-micro` VM instance with Debian 11.
  - Attaches a startup script for initialization.



## Project Structure

```
.
├── app.py                 # Discord bot implementation
├── Dockerfile             # Docker image configuration
├── requirements.txt       # Python dependencies
├── .env                   # Environment variables
├── terraform/
│   ├── main.tf            # Terraform configuration
│   ├── variables.tf       # Input variables
│   └── startup_script.sh  # VM initialization script
├── README.md              # Project documentation
```