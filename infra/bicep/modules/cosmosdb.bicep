// Cosmos DB deployment with containers for MCP data
param location string
param baseName string
param environmentName string
param tags object

@description('Enable private endpoint + private DNS (disables public network access)')
param enablePrivateEndpoint bool = false

@description('Subnet resource ID used for the Cosmos DB private endpoint')
param privateEndpointSubnetId string = ''

@description('Private DNS zone resource ID for privatelink.documents.azure.com')
param privateDnsZoneId string = ''

var agentStateContainerName = 'workshop_agent_state_store'


var cosmosDbName = '${baseName}-${environmentName}-cosmos'
var databaseName = 'contoso'

resource cosmosDb 'Microsoft.DocumentDB/databaseAccounts@2025-10-15' = {
  name: cosmosDbName
  location: location
  kind: 'GlobalDocumentDB'
  properties: {
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    databaseAccountOfferType: 'Standard'
    disableLocalAuth: false
    locations: [
      {
        failoverPriority: 0
        isZoneRedundant: false
        locationName: location
      }
    ]
    capabilities: [
      {
        name: 'EnableNoSQLVectorSearch'
      }
    ]
    publicNetworkAccess: enablePrivateEndpoint ? 'Disabled' : 'Enabled'
  }
  tags: tags
}

resource database 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases@2025-10-15' = {
  parent: cosmosDb
  name: databaseName
  properties: {
    resource: {
      id: databaseName
    }
  }
}

// Customers container
resource customersContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2025-10-15' = {
  parent: database
  name: 'Customers'
  properties: {
    resource: {
      id: 'Customers'
      partitionKey: {
        paths: ['/customer_id']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
      }
    }
  }
}

// Subscriptions container
resource subscriptionsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2025-10-15' = {
  parent: database
  name: 'Subscriptions'
  properties: {
    resource: {
      id: 'Subscriptions'
      partitionKey: {
        paths: ['/customer_id']
        kind: 'Hash'
      }
    }
  }
}

// Products container
resource productsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2025-10-15' = {
  parent: database
  name: 'Products'
  properties: {
    resource: {
      id: 'Products'
      partitionKey: {
        paths: ['/category']
        kind: 'Hash'
      }
    }
  }
}

// Promotions container
resource promotionsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2025-10-15' = {
  parent: database
  name: 'Promotions'
  properties: {
    resource: {
      id: 'Promotions'
      partitionKey: {
        paths: ['/id']
        kind: 'Hash'
      }
    }
  }
}

// Agent State Store container
resource agentStateContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2025-10-15' = {
  parent: database
  name: agentStateContainerName
  properties: {
    resource: {
      id: agentStateContainerName
      partitionKey: {
        paths: [
          '/tenant_id'
          '/id'
        ]
        kind: 'MultiHash'
        version: 2
      }
    }
  }
}

// Invoices container
resource invoicesContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2025-10-15' = {
  parent: database
  name: 'Invoices'
  properties: {
    resource: {
      id: 'Invoices'
      partitionKey: {
        paths: ['/subscription_id']
        kind: 'Hash'
      }
    }
  }
}

// Payments container
resource paymentsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2025-10-15' = {
  parent: database
  name: 'Payments'
  properties: {
    resource: {
      id: 'Payments'
      partitionKey: {
        paths: ['/invoice_id']
        kind: 'Hash'
      }
    }
  }
}

// SecurityLogs container
resource securityLogsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2025-10-15' = {
  parent: database
  name: 'SecurityLogs'
  properties: {
    resource: {
      id: 'SecurityLogs'
      partitionKey: {
        paths: ['/customer_id']
        kind: 'Hash'
      }
    }
  }
}

// Orders container
resource ordersContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2025-10-15' = {
  parent: database
  name: 'Orders'
  properties: {
    resource: {
      id: 'Orders'
      partitionKey: {
        paths: ['/customer_id']
        kind: 'Hash'
      }
    }
  }
}

// SupportTickets container
resource supportTicketsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2025-10-15' = {
  parent: database
  name: 'SupportTickets'
  properties: {
    resource: {
      id: 'SupportTickets'
      partitionKey: {
        paths: ['/customer_id']
        kind: 'Hash'
      }
    }
  }
}

// DataUsage container
resource dataUsageContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2025-10-15' = {
  parent: database
  name: 'DataUsage'
  properties: {
    resource: {
      id: 'DataUsage'
      partitionKey: {
        paths: ['/subscription_id']
        kind: 'Hash'
      }
    }
  }
}

// ServiceIncidents container
resource serviceIncidentsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2025-10-15' = {
  parent: database
  name: 'ServiceIncidents'
  properties: {
    resource: {
      id: 'ServiceIncidents'
      partitionKey: {
        paths: ['/id']
        kind: 'Hash'
      }
    }
  }
}

// KnowledgeDocuments container (for RAG/vector search)
resource knowledgeDocumentsContainer 'Microsoft.DocumentDB/databaseAccounts/sqlDatabases/containers@2025-10-15' = {
  parent: database
  name: 'KnowledgeDocuments'
  properties: {
    resource: {
      id: 'KnowledgeDocuments'
      partitionKey: {
        paths: ['/category']
        kind: 'Hash'
      }
      indexingPolicy: {
        indexingMode: 'consistent'
        automatic: true
        includedPaths: [
          {
            path: '/*'
          }
        ]
        excludedPaths: [
          {
            path: '/embedding/*'
          }
        ]
      }
    }
  }
}

// Private endpoint & DNS configuration
var privateEndpointName = '${cosmosDbName}-pe'
var privateDnsZoneGroupName = 'cosmosdb-zone-group'

resource cosmosPrivateEndpoint 'Microsoft.Network/privateEndpoints@2023-05-01' = if (enablePrivateEndpoint) {
  name: privateEndpointName
  location: location
  properties: {
    privateLinkServiceConnections: [
      {
        name: 'cosmosdb'
        properties: {
          privateLinkServiceId: cosmosDb.id
          groupIds: [
            'Sql'
          ]
        }
      }
    ]
    subnet: {
      id: privateEndpointSubnetId
    }
  }
  tags: tags
}

resource cosmosPrivateDnsZoneGroup 'Microsoft.Network/privateEndpoints/privateDnsZoneGroups@2023-05-01' = if (enablePrivateEndpoint) {
  parent: cosmosPrivateEndpoint
  name: privateDnsZoneGroupName
  properties: {
    privateDnsZoneConfigs: [
      {
        name: 'documents'
        properties: {
          privateDnsZoneId: privateDnsZoneId
        }
      }
    ]
  }
}

output endpoint string = cosmosDb.properties.documentEndpoint
@secure()
output primaryKey string = cosmosDb.listKeys().primaryMasterKey
output databaseName string = databaseName
output accountName string = cosmosDb.name
output accountId string = cosmosDb.id
output agentStateContainer string = agentStateContainerName
