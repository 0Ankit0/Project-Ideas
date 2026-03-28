# C4 Component Diagram

This document provides a C4 level-3 component view for the CRM application container.

## CRM Application Container – Components
```mermaid
flowchart TB
    subgraph Users[Users]
      SalesRep[Sales Representative]
      Manager[Sales Manager]
      Admin[CRM Admin]
    end

    subgraph CRM[CRM Application Container]
      UIBFF[Web UI + BFF]
      LeadCmp[Lead Management Component]
      AccountCmp[Account/Contact Component]
      OppCmp[Opportunity Pipeline Component]
      ActivityCmp[Activity Timeline Component]
      ForecastCmp[Forecasting Component]
      TerritoryCmp[Territory Management Component]
      AuthCmp[AuthZ + Policy Component]
      AuditCmp[Audit & Compliance Component]
      IntegrationCmp[Integration Orchestrator]
    end

    subgraph DataInfra[Data and Infra Containers]
      OLTP[(CRM OLTP Database)]
      Cache[(Redis Cache)]
      Bus[(Event Bus)]
      Search[(Search Index)]
      DW[(Analytics Warehouse)]
    end

    SalesRep --> UIBFF
    Manager --> UIBFF
    Admin --> UIBFF

    UIBFF --> AuthCmp
    UIBFF --> LeadCmp
    UIBFF --> AccountCmp
    UIBFF --> OppCmp
    UIBFF --> ActivityCmp
    UIBFF --> ForecastCmp
    UIBFF --> TerritoryCmp

    LeadCmp --> OLTP
    AccountCmp --> OLTP
    OppCmp --> OLTP
    ActivityCmp --> OLTP
    ForecastCmp --> OLTP
    TerritoryCmp --> OLTP

    LeadCmp --> Bus
    OppCmp --> Bus
    ForecastCmp --> Bus
    TerritoryCmp --> Bus

    IntegrationCmp --> Bus
    IntegrationCmp --> Search
    IntegrationCmp --> DW

    AuthCmp --> Cache
    AuditCmp --> OLTP
    AuditCmp --> DW
```

## Component Responsibilities
- **UI + BFF**: session-aware API facade for web/mobile channels.
- **Lead/Account/Opportunity/Activity components**: transactional domain execution.
- **Forecast + Territory components**: managerial controls, rollups, and reassignment workflows.
- **AuthZ + Policy**: central authorization checks and policy decisioning.
- **Audit & Compliance**: immutable event journaling for sensitive actions.
- **Integration Orchestrator**: async sync/replay between CRM and external systems.
