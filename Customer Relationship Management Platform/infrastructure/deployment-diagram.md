# Deployment Diagram

## Production Deployment Topology
```mermaid
flowchart TB
    Internet[(Internet)] --> WAF[WAF + CDN]
    WAF --> ALB[Public Load Balancer]

    subgraph VPC[Production VPC]
      subgraph Public[Public Subnet]
        ALB
      end

      subgraph PrivateApp[Private App Subnets]
        API[API Pods]
        Worker[Async Worker Pods]
      end

      subgraph PrivateData[Private Data Subnets]
        RDS[(PostgreSQL - Primary/Replica)]
        Redis[(Redis Cluster)]
        MQ[(Managed Message Broker)]
        Search[(Search Cluster)]
      end
    end

    ALB --> API
    API --> RDS
    API --> Redis
    API --> MQ

    Worker --> RDS
    Worker --> MQ
    Worker --> Search

    API --> Logs[Centralized Logs/Tracing]
    Worker --> Logs
    RDS --> Backup[Encrypted Backups]
```

## Environment Promotion
```mermaid
flowchart LR
    Dev[Dev] --> Stage[Stage]
    Stage --> Prod[Prod]
    Stage -->|Smoke + Contract Tests| Gate1[Release Gate]
    Gate1 --> Prod
```

## Domain Glossary
- **Deployment Topology**: File-specific term used to anchor decisions in **Deployment Diagram**.
- **Lead**: Prospect record entering qualification and ownership workflows.
- **Opportunity**: Revenue record tracked through pipeline stages and forecast rollups.
- **Correlation ID**: Trace identifier propagated across APIs, queues, and audits for this workflow.

## Entity Lifecycles
- Lifecycle for this document: `Build Artifact -> Promote -> Deploy -> Verify -> Rollback/Finalize`.
- Each transition must capture actor, timestamp, source state, target state, and justification note.

```mermaid
flowchart LR
    A[Build Artifact] --> B[Promote]
    B[Promote] --> C[Deploy]
    C[Deploy] --> D[Verify]
    D[Verify] --> E[Rollback/Finalize]
    E[Rollback/Finalize]
```

## Integration Boundaries
- Boundaries include CI/CD, registry, cluster scheduler, and ingress.
- Data ownership and write authority must be explicit at each handoff boundary.
- Interface changes require schema/version review and downstream impact acknowledgement.

## Error and Retry Behavior
- Canary failure triggers automatic rollback and retry in next window only.
- Retries must preserve idempotency token and correlation ID context.
- Exhausted retries route to an operational queue with triage metadata.

## Measurable Acceptance Criteria
- Deployment doc includes rollback objective <=15 min and blast-radius notes.
- Observability must publish latency, success rate, and failure-class metrics for this document's scope.
- Quarterly review confirms definitions and diagrams still match production behavior.
