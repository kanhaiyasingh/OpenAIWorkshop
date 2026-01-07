# Azure Infrastructure Deployment

This directory contains Infrastructure as Code (IaC) for deploying the OpenAI Workshop application to Azure using either **Terraform** or **Bicep**.

## Architecture Overview

The deployment creates a secure, enterprise-ready architecture with the following components:

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                              Azure Resource Group                                │
│                                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────────────┐│
│  │                    Virtual Network (10.10.0.0/16)                           ││
│  │                                                                             ││
│  │  ┌─────────────────────────────────────────────────────────────────────┐   ││
│  │  │           Container Apps Subnet (10.10.0.0/23)                      │   ││
│  │  │                                                                     │   ││
│  │  │  ┌─────────────────────────────────────────────────────────────┐   │   ││
│  │  │  │         Container Apps Environment                          │   │   ││
│  │  │  │                                                             │   │   ││
│  │  │  │  ┌─────────────────┐         ┌─────────────────┐           │   │   ││
│  │  │  │  │  Backend App    │────────▶│  MCP Service    │           │   │   ││
│  │  │  │  │  (Public)       │ internal│  (Internal)     │           │   │   ││
│  │  │  │  └────────┬────────┘         └────────┬────────┘           │   │   ││
│  │  │  │           │                           │                     │   │   ││
│  │  │  └───────────┼───────────────────────────┼─────────────────────┘   │   ││
│  │  │              │                           │                         │   ││
│  │  └──────────────┼───────────────────────────┼─────────────────────────┘   ││
│  │                 │                           │                             ││
│  │  ┌──────────────┼───────────────────────────┼─────────────────────────┐   ││
│  │  │              │  Private Endpoints Subnet (10.10.2.0/24)            │   ││
│  │  │              │                           │                         │   ││
│  │  │     ┌────────▼────────┐         ┌────────▼────────┐               │   ││
│  │  │     │  Cosmos DB PE   │         │  OpenAI PE      │               │   ││
│  │  │     │  (Private)      │         │  (Private)      │               │   ││
│  │  │     └─────────────────┘         └─────────────────┘               │   ││
│  │  │                                                                    │   ││
│  │  └────────────────────────────────────────────────────────────────────┘   ││
│  │                                                                             ││
│  └─────────────────────────────────────────────────────────────────────────────┘│
│                                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐              │
│  │  Azure OpenAI    │  │  Cosmos DB       │  │  Container       │              │
│  │  (AI Services)   │  │  (NoSQL)         │  │  Registry        │              │
│  │  - GPT Model     │  │  - Customers     │  │  (ACR)           │              │
│  │  - Embedding     │  │  - Products      │  │                  │              │
│  │                  │  │  - Agent State   │  │                  │              │
│  └──────────────────┘  └──────────────────┘  └──────────────────┘              │
│                                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐                                    │
│  │  Log Analytics   │  │  Managed         │                                    │
│  │  Workspace       │  │  Identities      │                                    │
│  └──────────────────┘  └──────────────────┘                                    │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## Security Features

### Network Security

| Feature | Description | Configuration |
|---------|-------------|---------------|
| **VNet Integration** | Container Apps run inside a dedicated VNet | `enable_networking = true` |
| **Private Endpoints** | Cosmos DB and OpenAI accessed via private endpoints | `enable_private_endpoint = true` |
| **Internal MCP** | MCP service is internal-only, not exposed to internet | `mcp_internal_only = true` |
| **Subnet Isolation** | Separate subnets for apps and private endpoints | `/23` for apps, `/24` for PEs |

### Identity & Access

| Feature | Description | Configuration |
|---------|-------------|---------------|
| **Managed Identity** | Apps use managed identity to access Azure services | `use_cosmos_managed_identity = true` |
| **RBAC for Cosmos DB** | Data plane access via Cosmos DB RBAC roles | Automatic with managed identity |
| **RBAC for OpenAI** | Cognitive Services OpenAI User role | Automatic with managed identity |
| **No API Keys** | No secrets stored in environment variables | Managed identity authentication |

### Container Apps Security

| Feature | Description |
|---------|-------------|
| **User-Assigned Identity** | Each app has its own managed identity |
| **ACR Pull via Identity** | Images pulled using managed identity (no registry passwords) |
| **Internal Communication** | Backend reaches MCP via internal URL |
| **HTTPS Ingress** | Public endpoints use HTTPS with managed certificates |

## Directory Structure

```
infra/
├── README.md                    # This file
├── terraform/                   # Terraform configuration
│   ├── deploy.ps1              # Deployment script
│   ├── dev.tfvars              # Development environment variables
│   ├── main.tf                 # Core resources (RG, OpenAI)
│   ├── network.tf              # VNet, subnets, private endpoints
│   ├── cosmosdb.tf             # Cosmos DB with containers
│   ├── _aca.tf                 # Container Apps Environment
│   ├── _aca-be.tf              # Backend Container App
│   ├── _aca-mcp.tf             # MCP Container App
│   ├── _acr.tf                 # Container Registry
│   ├── variables.tf            # Variable definitions
│   ├── outputs.tf              # Output values
│   └── providers.tf            # Provider configuration
│
└── bicep/                       # Bicep configuration
    ├── deploy.ps1              # Deployment script
    ├── main.bicep              # Main orchestrator
    ├── parameters/             # Environment parameters
    │   ├── dev.bicepparam
    │   ├── staging.bicepparam
    │   └── prod.bicepparam
    └── modules/                # Modular templates
        ├── openai.bicep
        ├── cosmosdb.bicep
        ├── network.bicep
        ├── container-apps-environment.bicep
        ├── mcp-service.bicep
        └── application.bicep
```

## Quick Start

### Prerequisites

1. **Azure CLI**: Install from https://aka.ms/azure-cli
2. **Terraform** (for Terraform deployment): Install from https://terraform.io
3. **Docker**: Required for building container images
4. **PowerShell 7+**: For running deployment scripts
5. **Azure Subscription**: With Owner or Contributor + User Access Administrator roles

### Login to Azure

```powershell
az login
az account set --subscription <subscription-id>
```

## Deployment Options

### Option 1: Terraform (Recommended)

#### Basic Deployment

```powershell
cd infra/terraform
./deploy.ps1 -Environment dev
```

#### With All Security Features Enabled

Edit `dev.tfvars`:

```hcl
# Core settings
environment      = "dev"
location         = "eastus2"
project_name     = "OpenAIWorkshop"

# Security: Managed Identity (no API keys)
use_cosmos_managed_identity = true

# Security: VNet Integration
enable_networking       = true
enable_private_endpoint = true

# Security: Internal MCP Service
mcp_internal_only = true

# OpenAI Configuration
create_openai_deployment = true
openai_deployment_name   = "gpt-4.1"
openai_model_name        = "gpt-4.1"
openai_model_version     = "2025-04-14"
```

Then deploy:

```powershell
./deploy.ps1 -Environment dev
```

### Option 2: Bicep

#### Basic Deployment

```powershell
cd infra/bicep
./deploy.ps1 -Environment dev
```

#### With Security Features

```powershell
./deploy.ps1 -Environment dev -EnableNetworking -EnablePrivateEndpoints
```

Or edit `parameters/dev.bicepparam`:

```bicep
using '../main.bicep'

param location = 'eastus2'
param environmentName = 'dev'
param baseName = 'openai-workshop'
param useCosmosManagedIdentity = true
param enableNetworking = true
param enablePrivateEndpoints = true
```

## Configuration Reference

### Terraform Variables

#### Core Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `project_name` | string | `OpenAIWorkshop` | Base name for resources |
| `location` | string | `eastus2` | Azure region |
| `environment` | string | `dev` | Environment name |
| `iteration` | string | `001` | Iteration suffix (prevents soft-delete conflicts) |

#### Security Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `use_cosmos_managed_identity` | bool | `true` | Use managed identity for Cosmos DB (recommended) |
| `enable_networking` | bool | `false` | Deploy VNet with Container Apps integration |
| `enable_private_endpoint` | bool | `false` | Use private endpoints for Cosmos DB and OpenAI |
| `mcp_internal_only` | bool | `false` | Make MCP service internal-only |

#### Networking Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `vnet_address_prefix` | string | `10.10.0.0/16` | VNet address space |
| `container_apps_subnet_prefix` | string | `10.10.0.0/23` | Container Apps subnet (min /23) |
| `private_endpoint_subnet_prefix` | string | `10.10.2.0/24` | Private endpoints subnet |

#### OpenAI Settings

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `create_openai_deployment` | bool | `true` | Create OpenAI model deployment |
| `openai_deployment_name` | string | `gpt-4.1` | Deployment name |
| `openai_model_name` | string | `gpt-4.1` | Model name |
| `openai_model_version` | string | `2025-04-14` | Model version |
| `create_openai_embedding_deployment` | bool | `false` | Create embedding deployment |

## Security Profiles

### Development (Minimal Security)

```hcl
use_cosmos_managed_identity = true
enable_networking           = false
enable_private_endpoint     = false
mcp_internal_only          = false
```

- ✅ Managed identity for Cosmos DB
- ❌ Public network access for all services
- ❌ MCP accessible from internet

### Staging (Enhanced Security)

```hcl
use_cosmos_managed_identity = true
enable_networking           = true
enable_private_endpoint     = false
mcp_internal_only          = true
```

- ✅ Managed identity
- ✅ VNet integration for Container Apps
- ✅ MCP internal-only
- ❌ Services still use public endpoints

### Production (Full Security)

```hcl
use_cosmos_managed_identity = true
enable_networking           = true
enable_private_endpoint     = true
mcp_internal_only          = true
```

- ✅ Managed identity (no API keys)
- ✅ VNet integration
- ✅ Private endpoints for Cosmos DB and OpenAI
- ✅ MCP internal-only
- ✅ No public network access to backend services

## Architecture Deep Dive

### Container Apps Communication

When `mcp_internal_only = true` and `enable_networking = true`:

```
Internet
    │
    ▼
┌─────────────────────────────────────────────────────────┐
│  Container Apps Environment (VNet Integrated)           │
│                                                         │
│  ┌─────────────────┐         ┌─────────────────┐       │
│  │  Backend App    │────────▶│  MCP Service    │       │
│  │                 │  http:// │                 │       │
│  │  Ingress:       │  internal│  Ingress:       │       │
│  │  external=true  │  URL     │  external=false │       │
│  │  (HTTPS)        │         │  (HTTP internal)│       │
│  └─────────────────┘         └─────────────────┘       │
│                                     │                   │
└─────────────────────────────────────┼───────────────────┘
                                      │
                                      ▼
                              Private Endpoints
                              (Cosmos DB, OpenAI)
```

### Private Endpoint DNS Resolution

Private DNS zones are created and linked to the VNet:

| Service | Private DNS Zone |
|---------|-----------------|
| Cosmos DB | `privatelink.documents.azure.com` |
| Azure OpenAI | `privatelink.openai.azure.com` |

When apps resolve service FQDNs, they get private IP addresses instead of public IPs.

### Managed Identity Flow

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  Container App  │────▶│  Azure AD       │────▶│  Azure Service  │
│  (with UAMI)    │     │  (Token)        │     │  (RBAC Check)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                                               │
        │  Uses token, no API keys                      │
        └───────────────────────────────────────────────┘
```

Role assignments:
- **Cosmos DB**: `Cosmos DB Built-in Data Contributor`
- **Azure OpenAI**: `Cognitive Services OpenAI User`
- **Container Registry**: `AcrPull`

## Outputs

After deployment, these values are available:

### Terraform

```powershell
terraform output

# Key outputs:
# - be_aca_url         = Backend application URL
# - mcp_aca_url        = MCP service URL (internal if mcp_internal_only=true)
# - cosmos_endpoint    = Cosmos DB endpoint
# - openai_endpoint    = Azure OpenAI endpoint
# - acr_login_server   = Container Registry login server
```

### Bicep

Outputs are displayed after deployment and saved to `deployment-outputs.json`.

## Troubleshooting

### Container App Logs

```powershell
# Backend logs
az containerapp logs show --name ca-be-002 --resource-group rg-OpenAIWorkshop-dev-002 --follow

# MCP logs
az containerapp logs show --name ca-mcp-002 --resource-group rg-OpenAIWorkshop-dev-002 --follow
```

### Validate Configuration

```powershell
# Terraform
cd infra/terraform
terraform validate

# Bicep
cd infra/bicep
az deployment sub validate --location eastus2 --template-file main.bicep --parameters parameters/dev.bicepparam
```

### Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Container App fails to start | Missing role assignments | Wait for RBAC propagation (~2 min) |
| Cannot reach Cosmos DB | Private endpoint DNS not resolving | Verify private DNS zone is linked to VNet |
| MCP unreachable from backend | Wrong URL format | Check if using internal URL when `mcp_internal_only=true` |
| Deployment quota exceeded | OpenAI TPM limits | Reduce `openai_deployment_capacity` or request quota increase |

## Cleanup

### Delete All Resources

```powershell
# Terraform
cd infra/terraform
terraform destroy -var-file=dev.tfvars

# Bicep
az group delete --name openai-workshop-dev-rg --yes
```

## Additional Resources

- [Azure Container Apps Documentation](https://learn.microsoft.com/azure/container-apps/)
- [Azure OpenAI Documentation](https://learn.microsoft.com/azure/ai-services/openai/)
- [Azure Private Link Documentation](https://learn.microsoft.com/azure/private-link/)
- [Terraform AzureRM Provider](https://registry.terraform.io/providers/hashicorp/azurerm/latest/docs)
- [Bicep Documentation](https://learn.microsoft.com/azure/azure-resource-manager/bicep/)
