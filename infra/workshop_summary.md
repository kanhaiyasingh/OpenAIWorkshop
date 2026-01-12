# Enterprise-Ready Agentic AI Infrastructure Workshop

**Build and deploy secure, end-to-end agentic AI solutions on Azure**

---

## Who Is This For

Infrastructure engineers and enterprise architects with in-depth Azure knowledge who need to deploy agentic AI in an enterprise-grade manner.

---

## What You'll Learn

- ✅ **End-to-end agentic architecture** — MCP tools → Agent orchestration → Backend → Frontend
- ✅ **Your choice of IaC** — Bicep or Terraform, manual scripts or GitHub Actions
- ✅ **Modern identity principles** — OIDC for GitHub Actions, Managed Identity for Azure services (no keys)
- ✅ **Network isolation** — VNet with private endpoints, only frontend exposed to internet
- ✅ **Enterprise-ready template** — Scalable, reusable blueprint for standalone or landing zone deployment

---

## Why It Matters

Most agentic AI samples stop at proof-of-concept — public endpoints, API keys, no network isolation. This workshop provides a **repeatable, production-ready blueprint** from Dev → Prod.

---

## Architecture Diagram

```mermaid
flowchart LR

    User["👤 Users"]
    
    subgraph VNET["🛡️ Enterprise VNet"]
        direction LR
        
        subgraph AGENTS["🤖 Agentic Layer"]
            FE["🌐 Frontend"]
            BE["⚙️ Agent Orchestrator"]
            MCP["🔧 MCP Tools"]
        end
        
        subgraph DATA["☁️ Azure Services"]
            AOAI["🧠 OpenAI"]
            COSMOS["💾 Cosmos DB"]
        end
        
        subgraph SEC["🔐 Zero Trust"]
            MI["🎫 Managed Identity"]
            CICD["🚀 CI/CD"]
        end
    end

    User -->|HTTPS| FE
    FE --> BE
    BE --> MCP
    BE --> AOAI
    MCP --> COSMOS
    
    MI -.-> BE
    MI -.-> MCP
    CICD -.-> AGENTS

    %% Styling
    classDef user fill:#1976D2,stroke:#0D47A1,stroke-width:3px,color:#fff
    classDef frontend fill:#43A047,stroke:#1B5E20,stroke-width:2px,color:#fff
    classDef agents fill:#FF9800,stroke:#E65100,stroke-width:2px,color:#000
    classDef data fill:#9C27B0,stroke:#4A148C,stroke-width:2px,color:#fff
    classDef security fill:#00ACC1,stroke:#006064,stroke-width:2px,color:#fff

    class User user
    class FE frontend
    class BE,MCP agents
    class AOAI,COSMOS data
    class MI,CICD security
```