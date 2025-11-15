using './main.azd.bicep'

param environmentName = readEnvironmentVariable('AZURE_ENV_NAME', 'openaiworkshop')
param location = readEnvironmentVariable('AZURE_LOCATION', 'westus')
param mcpImageName = readEnvironmentVariable('SERVICE_MCP_IMAGE_NAME', '')
param appImageName = readEnvironmentVariable('SERVICE_APP_IMAGE_NAME', '')
param aadTenantId = readEnvironmentVariable('AAD_TENANT_ID', '')
param aadFrontendClientId = readEnvironmentVariable('AAD_FRONTEND_CLIENT_ID', '')
param aadApiAudience = readEnvironmentVariable('AAD_API_AUDIENCE', '')
param allowedEmailDomain = readEnvironmentVariable('AAD_ALLOWED_DOMAIN', 'microsoft.com')
param disableAuthSetting = readEnvironmentVariable('DISABLE_AUTH', 'false')
