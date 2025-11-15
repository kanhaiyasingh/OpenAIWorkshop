// Application Container App (Backend FastAPI + Frontend Node)
@description('Azure region for deployment')
param location string

@description('Base name for resources')
param baseName string

@description('Container Apps Environment resource ID')
param containerAppsEnvironmentId string

@description('Container Registry name')
param containerRegistryName string

@description('Azure OpenAI endpoint URL')
param azureOpenAIEndpoint string

@description('Azure OpenAI API key')
@secure()
param azureOpenAIKey string

@description('Azure OpenAI deployment name')
param azureOpenAIDeploymentName string

@description('Azure OpenAI embedding deployment name')
param azureOpenAIEmbeddingDeploymentName string

@description('MCP service URL')
param mcpServiceUrl string

@description('Resource tags')
param tags object

@description('AAD tenant ID used for authentication enforcement. Empty to fallback to the current tenant context.')
param aadTenantId string = ''

@description('Public client ID requesting tokens (frontend).')
param aadClientId string = ''

@description('App ID URI (audience) for the protected API.')
param aadApiAudience string = ''

@description('Whether to disable auth in the backend.')
param disableAuth bool = true

@description('Allowed e-mail domain for authenticated users when auth is enabled.')
param allowedEmailDomain string = 'microsoft.com'

@description('Container image tag')
param imageTag string = 'latest'

@description('Full container image name from azd')
param imageName string = ''

var appName = '${baseName}-app'
var containerImage = !empty(imageName) ? imageName : '${containerRegistryName}.azurecr.io/workshop-app:${imageTag}'
var azdTags = union(tags, {
  'azd-service-name': 'app'
  'azd-service-type': 'containerapp'
})
var effectiveTenantId = !empty(aadTenantId) ? aadTenantId : tenant().tenantId
var apiAudience = aadApiAudience
var aadAuthority = !empty(effectiveTenantId) ? '${environment().authentication.loginEndpoint}${effectiveTenantId}' : ''

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-01-01-preview' existing = {
  name: containerRegistryName
}

resource application 'Microsoft.App/containerApps@2023-05-01' = {
  name: appName
  location: location
  properties: {
    managedEnvironmentId: containerAppsEnvironmentId
    configuration: {
      ingress: {
        external: true
        targetPort: 3000
        transport: 'http'
        allowInsecure: false
        corsPolicy: {
          allowedOrigins: ['*']
          allowedMethods: ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
          allowedHeaders: ['*']
          allowCredentials: true
        }
      }
      registries: [
        {
          server: containerRegistry.properties.loginServer
          username: containerRegistry.listCredentials().username
          passwordSecretRef: 'registry-password'
        }
      ]
      secrets: [
        {
          name: 'registry-password'
          value: containerRegistry.listCredentials().passwords[0].value
        }
        {
          name: 'azure-openai-key'
          value: azureOpenAIKey
        }
      ]
    }
    template: {
      containers: [
        {
          name: 'backend'
          image: containerImage
          resources: {
            cpu: json('1.0')
            memory: '2Gi'
          }
          env: [
            {
              name: 'AZURE_OPENAI_ENDPOINT'
              value: azureOpenAIEndpoint
            }
            {
              name: 'AZURE_OPENAI_API_KEY'
              secretRef: 'azure-openai-key'
            }
            {
              name: 'AZURE_OPENAI_CHAT_DEPLOYMENT'
              value: azureOpenAIDeploymentName
            }
            {
              name: 'AZURE_OPENAI_EMBEDDING_DEPLOYMENT'
              value: azureOpenAIEmbeddingDeploymentName
            }
            {
              name: 'AZURE_OPENAI_API_VERSION'
              value: '2025-03-01-preview'
            }
            {
              name: 'OPENAI_MODEL_NAME'
              value: 'gpt-5-chat'
            }
            {
              name: 'MCP_SERVER_URI'
              value: mcpServiceUrl
            }
            {
              name: 'DISABLE_AUTH'
              value: string(disableAuth)
            }
            {
              name: 'AGENT_MODULE'
              value: 'agents.agent_framework.single_agent'
            }
            {
              name: 'MAGENTIC_LOG_WORKFLOW_EVENTS'
              value: 'true'
            }
            {
              name: 'MAGENTIC_ENABLE_PLAN_REVIEW'
              value: 'true'
            }
            {
              name: 'MAGENTIC_MAX_ROUNDS'
              value: '10'
            }
            {
              name: 'HANDOFF_CONTEXT_TRANSFER_TURNS'
              value: '-1'
            }
            {
              name: 'AAD_TENANT_ID'
              value: effectiveTenantId
            }
            {
              name: 'TENANT_ID'
              value: effectiveTenantId
            }
            {
              name: 'CLIENT_ID'
              value: aadClientId
            }
            {
              name: 'AUTHORITY'
              value: aadAuthority
            }
            {
              name: 'MCP_API_AUDIENCE'
              value: apiAudience
            }
            {
              name: 'AAD_API_SCOPE'
              value: !empty(apiAudience) ? '${apiAudience}/user_impersonation' : ''
            }
            {
              name: 'ALLOWED_EMAIL_DOMAIN'
              value: allowedEmailDomain
            }
          ]
        }
      ]
      scale: {
        minReplicas: 1
        maxReplicas: 5
        rules: [
          {
            name: 'http-scaling'
            http: {
              metadata: {
                concurrentRequests: '20'
              }
            }
          }
        ]
      }
    }
  }
  tags: azdTags
}

output applicationUrl string = 'https://${application.properties.configuration.ingress.fqdn}'
output applicationName string = application.name
output fqdn string = application.properties.configuration.ingress.fqdn
