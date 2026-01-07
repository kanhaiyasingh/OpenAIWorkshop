# Development Environment Configuration
# Generated for OpenAI Workshop Terraform Deployment

project_name    = "OpenAIWorkshop"
environment     = "dev"
location        = "eastus2"
tenant_id       = "0fbe7234-45ea-498b-b7e4-1a8b2d3be4d9"
subscription_id = "840b5c5c-3f4a-459a-94fc-6bad2a969f9d"
iteration       = "002"  # Unique suffix for resource names

# Container Registry - create new one
create_acr = true
acr_sku    = "Basic"
acr_name   = "openaiworkshopdevacr"  # Only used if create_acr = false

# Container images - will use ACR once created
# Format: <acr_name>.azurecr.io/<image>:<tag>
# These will be updated after ACR is created and images are pushed
docker_image_backend = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"
docker_image_mcp     = "mcr.microsoft.com/azuredocs/containerapps-helloworld:latest"

# OpenAI Configuration
create_openai_deployment     = false  # Skip deployment due to quota (1000/1000 TPM used)
openai_deployment_name       = "gpt-5.2-chat"
openai_model_name            = "gpt-5.2-chat"
openai_model_version         = "2025-04-14"
openai_deployment_capacity   = 100
openai_embedding_deployment_name = "text-embedding-ada-002"

# Cosmos DB - use managed identity (recommended)
use_cosmos_managed_identity = true
enable_private_endpoint     = false

# Authentication - disabled for development
disable_auth         = true
aad_tenant_id        = ""
aad_client_id        = ""
aad_api_audience     = ""
allowed_email_domain = "microsoft.com"

# Container App ports
backend_target_port = 7000
mcp_target_port     = 8000

# Tags
tags = {
  Environment = "Development"
  Owner       = "DevTeam"
  CostCenter  = "Engineering"
}
