# Azure Infrastructure Deployment Script for OpenAI Workshop
# This script builds Docker images, pushes to ACR, and deploys infrastructure
#
# Usage:
#   .\deploy.ps1                           # Full deployment with defaults
#   .\deploy.ps1 -InfraOnly                # Deploy infra, skip container builds
#   .\deploy.ps1 -SkipBuild                # Deploy but skip container builds
#   .\deploy.ps1 -SeedCosmosData           # Seed Cosmos DB with sample data after deployment
#   .\deploy.ps1 -McpInternalOnly          # Make MCP service internal-only

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet('dev', 'staging', 'prod')]
    [string]$Environment = 'dev',
    
    [Parameter(Mandatory=$false)]
    [string]$Location = 'eastus2',
    
    [Parameter(Mandatory=$false)]
    [string]$BaseName = 'openai-workshop',
    
    [Parameter(Mandatory=$false)]
    [switch]$SkipBuild,
    
    [Parameter(Mandatory=$false)]
    [switch]$InfraOnly,

    [Parameter(Mandatory=$false)]
    [switch]$SeedCosmosData,

    [Parameter(Mandatory=$false)]
    [switch]$UseCosmosManagedIdentity,

    [Parameter(Mandatory=$false)]
    [switch]$McpInternalOnly
)

$ErrorActionPreference = 'Stop'

Write-Host "======================================" -ForegroundColor Cyan
Write-Host "Azure OpenAI Workshop Deployment" -ForegroundColor Cyan
Write-Host "Environment: $Environment" -ForegroundColor Cyan
Write-Host "Location: $Location" -ForegroundColor Cyan
Write-Host "Seed Cosmos Data: $SeedCosmosData" -ForegroundColor Cyan
Write-Host "Use Cosmos Managed Identity: $UseCosmosManagedIdentity" -ForegroundColor Cyan
Write-Host "MCP Internal Only: $McpInternalOnly" -ForegroundColor Cyan
Write-Host "======================================" -ForegroundColor Cyan

# Verify Azure CLI is logged in
$account = az account show 2>$null | ConvertFrom-Json
if (-not $account) {
    Write-Error "Not logged in to Azure CLI. Please run: az login"
    exit 1
}

# Variables
$ResourceGroupName = "$BaseName-$Environment-rg"
$SubscriptionId = $account.id
$AcrName = "$BaseName$Environment" + "acr" -replace '-', ''  # ACR names can't have hyphens

Write-Host "`nUsing Subscription: $SubscriptionId" -ForegroundColor Yellow
Write-Host "Using Tenant: $($account.tenantId)" -ForegroundColor Yellow
Write-Host "Logged in as: $($account.user.name)" -ForegroundColor Yellow

# Convert switch parameters to Bicep boolean strings
$seedCosmosDataParam = if ($SeedCosmosData) { "true" } else { "false" }
$useCosmosManagedIdentityParam = if ($UseCosmosManagedIdentity) { "true" } else { "true" }  # Default to true
$mcpInternalOnlyParam = if ($McpInternalOnly) { "true" } else { "false" }

# Step 1: Deploy Infrastructure
Write-Host "`n[1/5] Deploying Azure Infrastructure..." -ForegroundColor Green
az deployment sub create `
    --location $Location `
    --template-file $PSScriptRoot/main.bicep `
    --parameters location=$Location environmentName=$Environment baseName=$BaseName `
                 seedCosmosData=$seedCosmosDataParam useCosmosManagedIdentity=$useCosmosManagedIdentityParam `
                 mcpInternalOnly=$mcpInternalOnlyParam `
    --name "openai-workshop-$Environment-$(Get-Date -Format 'yyyyMMdd-HHmmss')" `
    --query 'properties.outputs' -o json | Out-File -FilePath "$PSScriptRoot/../../deployment-outputs.json"

if ($LASTEXITCODE -ne 0) {
    Write-Error "Infrastructure deployment failed!"
    exit 1
}

Write-Host "Infrastructure deployed successfully!" -ForegroundColor Green

# Read outputs
$outputs = Get-Content "$PSScriptRoot/../../deployment-outputs.json" | ConvertFrom-Json
$AcrLoginServer = "$AcrName.azurecr.io"

Write-Host "`nDeployment Outputs:" -ForegroundColor Yellow
Write-Host "  Resource Group: $($outputs.resourceGroupName.value)" -ForegroundColor Gray
Write-Host "  ACR Name: $AcrName" -ForegroundColor Gray
Write-Host "  ACR Login Server: $AcrLoginServer" -ForegroundColor Gray
Write-Host "  MCP Service URL: $($outputs.mcpServiceUrl.value)" -ForegroundColor Gray
Write-Host "  Application URL: $($outputs.applicationUrl.value)" -ForegroundColor Gray

if ($InfraOnly) {
    Write-Host "`nInfra-only mode: Skipping container builds and deployments" -ForegroundColor Yellow
    exit 0
}

# Step 2: Login to ACR
Write-Host "`n[2/5] Logging into Azure Container Registry..." -ForegroundColor Green
az acr login --name $AcrName

if ($LASTEXITCODE -ne 0) {
    Write-Error "ACR login failed!"
    exit 1
}

# Step 3: Build and Push MCP Service Image
if (-not $SkipBuild) {
    Write-Host "`n[3/5] Building and pushing MCP Service image..." -ForegroundColor Green
    
    Push-Location $PSScriptRoot/../../mcp
    try {
        docker build -t "$AcrLoginServer/mcp-service:latest" -f Dockerfile .
        docker push "$AcrLoginServer/mcp-service:latest"
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error "MCP Service image build/push failed!"
            exit 1
        }
    }
    finally {
        Pop-Location
    }
    
    Write-Host "MCP Service image built and pushed successfully!" -ForegroundColor Green
} else {
    Write-Host "`n[3/5] Skipping MCP Service build (--SkipBuild)" -ForegroundColor Yellow
}

# Step 4: Build and Push Application Image
if (-not $SkipBuild) {
    Write-Host "`n[4/5] Building and pushing Application image..." -ForegroundColor Green
    
    Push-Location $PSScriptRoot/../../agentic_ai
    try {
        docker build -t "$AcrLoginServer/workshop-app:latest" -f applications/Dockerfile .
        docker push "$AcrLoginServer/workshop-app:latest"
        
        if ($LASTEXITCODE -ne 0) {
            Write-Error "Application image build/push failed!"
            exit 1
        }
    }
    finally {
        Pop-Location
    }
    
    Write-Host "Application image built and pushed successfully!" -ForegroundColor Green
} else {
    Write-Host "`n[4/5] Skipping Application build (--SkipBuild)" -ForegroundColor Yellow
}

# Step 5: Update Container Apps with new images
Write-Host "`n[5/5] Updating Container Apps with new images..." -ForegroundColor Green

# Bicep naming pattern: {baseName}-{service}-{env}
$McpServiceName = "$BaseName-mcp-$Environment"
$AppName = "$BaseName-app-$Environment"

Write-Host "Updating MCP Service: $McpServiceName" -ForegroundColor Gray
az containerapp update `
    --resource-group $ResourceGroupName `
    --name $McpServiceName `
    --image "$AcrLoginServer/mcp-service:latest" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Note: MCP container app may need image refresh on next revision" -ForegroundColor Yellow
}

Write-Host "Updating Application: $AppName" -ForegroundColor Gray
az containerapp update `
    --resource-group $ResourceGroupName `
    --name $AppName `
    --image "$AcrLoginServer/workshop-app:latest" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "  Note: Application container app may need image refresh on next revision" -ForegroundColor Yellow
}

Write-Host "`n======================================" -ForegroundColor Cyan
Write-Host "Deployment Complete!" -ForegroundColor Green
Write-Host "======================================" -ForegroundColor Cyan
Write-Host "`nAccess your application at:" -ForegroundColor Yellow
Write-Host "  $($outputs.applicationUrl.value)" -ForegroundColor Cyan
Write-Host "`nMCP Service URL:" -ForegroundColor Yellow
Write-Host "  $($outputs.mcpServiceUrl.value)" -ForegroundColor Cyan
Write-Host "`nResource Group:" -ForegroundColor Yellow
Write-Host "  $ResourceGroupName" -ForegroundColor Cyan
