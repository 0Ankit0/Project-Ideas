# API Design

This document defines implementation-ready API contracts for the **Customer Relationship Management Platform**.

## API Surface Map
```mermaid
flowchart LR
    UI[Web/Mobile UI] --> GW[API Gateway]
    Integrations[External Integrations\nForms, Email, Calendar] --> GW

    GW --> LEAD[Lead Service API]
    GW --> CONTACT[Contact & Account API]
    GW --> OPP[Opportunity API]
    GW --> ACT[Activity API]
    GW --> FC[Forecast API]
    GW --> ADM[Admin/Territory API]

    LEAD --> EVT[(Event Bus)]
    CONTACT --> EVT
    OPP --> EVT
    ACT --> EVT
    FC --> EVT
    ADM --> EVT
```

## Core REST Endpoints (Representative)
```mermaid
classDiagram
    class LeadAPI {
      +POST /v1/leads
      +GET /v1/leads/{leadId}
      +PATCH /v1/leads/{leadId}
      +POST /v1/leads/{leadId}/qualify
      +POST /v1/leads/{leadId}/merge-candidates:search
    }

    class OpportunityAPI {
      +POST /v1/opportunities
      +GET /v1/opportunities/{opportunityId}
      +PATCH /v1/opportunities/{opportunityId}
      +POST /v1/opportunities/{opportunityId}/stage-transitions
      +POST /v1/opportunities/{opportunityId}/close
    }

    class ForecastAPI {
      +POST /v1/forecasts/snapshots
      +GET /v1/forecasts/snapshots/{snapshotId}
      +POST /v1/forecasts/snapshots/{snapshotId}/submit
      +POST /v1/forecasts/snapshots/{snapshotId}/approve
    }

    class TerritoryAPI {
      +POST /v1/territories/reassignments
      +GET /v1/territories/reassignments/{jobId}
    }
```

## Write Request Contract Pattern
```mermaid
sequenceDiagram
    autonumber
    participant C as API Client
    participant G as API Gateway
    participant S as Domain Service
    participant DB as Primary DB
    participant EB as Event Bus

    C->>G: POST /v1/opportunities/{id}/stage-transitions\nIdempotency-Key + Correlation-Id
    G->>S: Forward validated request context
    S->>DB: Upsert command log by Idempotency-Key
    alt Duplicate key
        DB-->>S: Existing result reference
        S-->>G: Return prior response (200/201)
    else New command
        S->>DB: Apply state transition transaction
        S->>EB: Publish OpportunityStageChanged
        S-->>G: Return success + resource version
    end
    G-->>C: HTTP response + Correlation-Id
```

## Reliability and Compliance Constraints
- All mutating endpoints require `Idempotency-Key` and `Correlation-Id` headers.
- Resource updates use optimistic concurrency via version/ETag fields.
- Sensitive reads and writes are RBAC-gated and mirrored into immutable audit logs.
- Async operations (merge, reassignment, backfill) return job resources and are pollable.
