# Deployment Diagram

## Overview
Production deployment architecture for the Finance Management System on AWS EKS, showing the mapping from software components to infrastructure nodes.

---

## Production Deployment Architecture

```mermaid
graph TB
    subgraph "Internet"
        Users[Finance Users]
    end

    subgraph "Edge Layer"
        R53[Route 53<br>DNS Failover]
        CF[CloudFront<br>Static Assets CDN]
        WAF[AWS WAF<br>Layer 7 Security]
    end

    subgraph "AWS Region (us-east-1)"
        subgraph "VPC (10.0.0.0/16)"
            subgraph "Public Subnets (AZ-a, AZ-b)"
                ALB[Application Load Balancer<br>HTTPS / TLS 1.3]
                NATGW[NAT Gateways]
            end

            subgraph "Private App Subnets (AZ-a, AZ-b)"
                subgraph "EKS Cluster"
                    subgraph "App Node Group"
                        FinanceAPI[Finance API Pod<br>FastAPI<br>HPA: 2-8 replicas]
                        WorkerPod[Worker Pod<br>Celery<br>HPA: 1-4 replicas]
                        WSPod[WebSocket Pod<br>FastAPI WS<br>2 replicas]
                    end

                    subgraph "System Pods"
                        Ingress[Nginx Ingress Controller]
                        ExtSecrets[External Secrets Operator<br>Syncs from Secrets Manager]
                        CertManager[Cert Manager]
                    end
                end
            end

            subgraph "Private Data Subnets (AZ-a, AZ-b)"
                subgraph "Database Tier"
                    RDSPrimary[(RDS PostgreSQL<br>Primary<br>db.r6g.2xlarge)]
                    RDSReplica[(RDS PostgreSQL<br>Read Replica<br>db.r6g.xlarge)]
                    AuditRDS[(Audit RDS<br>Append-Only<br>db.r6g.large)]
                    ElastiCache[(ElastiCache Redis<br>3-node Cluster)]
                end
            end
        end

        S3[S3 Buckets<br>Documents, Reports, Bank Files]
        SQS[SQS Queues<br>Report Jobs, Notifications]
        SecretsManager[Secrets Manager]
        KMS[KMS Keys]
    end

    subgraph "DR Region (us-west-2)"
        RDS_DR[(RDS Replica)]
        AuditRDS_DR[(Audit DR)]
        S3_DR[S3 CRR]
    end

    Users --> R53
    R53 --> CF
    CF --> WAF
    WAF --> ALB
    ALB --> Ingress
    Ingress --> FinanceAPI
    Ingress --> WSPod

    FinanceAPI --> RDSPrimary
    FinanceAPI --> AuditRDS
    FinanceAPI --> ElastiCache
    FinanceAPI --> S3
    FinanceAPI --> SQS
    FinanceAPI --> SecretsManager
    SecretsManager --> KMS
    KMS --> RDSPrimary

    SQS --> WorkerPod
    WorkerPod --> RDSPrimary
    WorkerPod --> S3

    RDSReplica -.->|Read queries| FinanceAPI

    RDSPrimary -.->|Replication| RDS_DR
    AuditRDS -.->|Replication| AuditRDS_DR
    S3 -.->|CRR| S3_DR
```

---

## Kubernetes Deployment Detail

```mermaid
graph TB
    subgraph "Kubernetes Namespace: finance-prod"
        subgraph "Ingress"
            NginxIngress[nginx-ingress-controller]
        end

        subgraph "Finance API Deployment"
            APISvc[finance-api Service<br>ClusterIP]
            APIPod1[finance-api Pod 1<br>FastAPI Container<br>CPU: 500m-2000m<br>Mem: 512Mi-2Gi]
            APIPod2[finance-api Pod 2]
            APIPod3[finance-api Pod 3]
            APIHPA[HorizontalPodAutoscaler<br>min:2 max:8<br>CPU: 70%]
        end

        subgraph "Worker Deployment"
            WorkerSvc[worker Service]
            WorkerPod1[worker Pod 1<br>Celery Worker<br>Queues: reports, payroll, notifications]
            WorkerPod2[worker Pod 2]
            WorkerHPA[HorizontalPodAutoscaler<br>min:1 max:4<br>Queue depth metric]
        end

        subgraph "WebSocket Deployment"
            WSSvc[websocket Service<br>ClusterIP]
            WSPod1[websocket Pod 1<br>FastAPI WS<br>Sticky sessions]
            WSPod2[websocket Pod 2]
        end

        subgraph "Config & Secrets"
            ConfigMap[ConfigMap<br>App Settings]
            Secret[Secret<br>Synced from AWS Secrets Manager]
            PVC[PersistentVolumeClaim<br>gp3 StorageClass]
        end
    end

    NginxIngress --> APISvc
    NginxIngress --> WSSvc
    APISvc --> APIPod1
    APISvc --> APIPod2
    APISvc --> APIPod3
    APIHPA --> APIPod1

    WorkerSvc --> WorkerPod1
    WorkerSvc --> WorkerPod2
    WorkerHPA --> WorkerPod1

    WSSvc --> WSPod1
    WSSvc --> WSPod2

    APIPod1 --> ConfigMap
    APIPod1 --> Secret
    WorkerPod1 --> ConfigMap
    WorkerPod1 --> Secret
```

---

## CI/CD Pipeline

```mermaid
graph LR
    subgraph "Source Control"
        Git[GitHub Repository]
    end

    subgraph "CI Pipeline (GitHub Actions)"
        Lint[Lint & Type Check<br>ruff, mypy]
        Test[Run Tests<br>pytest + coverage]
        SAST[SAST Scan<br>bandit, semgrep]
        Build[Docker Build<br>multi-stage]
        Scan[Container Scan<br>Amazon Inspector]
        Push[Push to ECR]
    end

    subgraph "CD Pipeline (ArgoCD)"
        ArgoProd[ArgoCD<br>Production Sync]
        K8sDeploy[kubectl apply<br>Rolling Update]
        HealthCheck[Readiness Check<br>/health /ready]
        Rollback[Auto-Rollback<br>on failure]
    end

    subgraph "Infrastructure"
        ECR[Amazon ECR]
        EKS[Amazon EKS]
    end

    Git --> Lint
    Lint --> Test
    Test --> SAST
    SAST --> Build
    Build --> Scan
    Scan --> Push
    Push --> ECR

    ECR --> ArgoProd
    ArgoProd --> K8sDeploy
    K8sDeploy --> EKS
    K8sDeploy --> HealthCheck
    HealthCheck -->|Unhealthy| Rollback
    Rollback --> EKS
```

## Implementation-Ready Finance Control Expansion

### 1) Accounting Rule Assumptions (Detailed)
- Ledger model is strictly double-entry with balanced journal headers and line-level dimensional tagging (entity, cost-center, project, product, counterparty).
- Posting policies are versioned and time-effective; historical transactions are evaluated against the rule version active at transaction time.
- Currency handling requires transaction currency, functional currency, and optional reporting currency; FX revaluation and realized/unrealized gains are separated.
- Materiality thresholds are explicit and configurable; below-threshold variances may auto-resolve only when policy explicitly allows.

### 2) Transaction Invariants and Data Contracts
- Every command/event must include `transaction_id`, `idempotency_key`, `source_system`, `event_time_utc`, `actor_id/service_principal`, and `policy_version`.
- Mutations affecting posted books are append-only. Corrections use reversal + adjustment entries with causal linkage to original posting IDs.
- Period invariant checks: no unapproved journals in closing period, all sub-ledger control accounts reconciled, and close checklist fully attested.
- Referential invariants: every ledger line links to a provenance artifact (invoice/payment/payroll/expense/asset/tax document).

### 3) Reconciliation and Close Strategy
- Continuous reconciliation cadence:
  - **T+0/T+1** operational reconciliation (gateway, bank, processor, payroll outputs).
  - **Daily** sub-ledger to GL tie-out.
  - **Monthly/Quarterly** close certification with controller sign-off.
- Exception taxonomy is mandatory: timing mismatch, mapping/config error, duplicate, missing source event, external counterparty variance, FX rounding.
- Close blockers are machine-detectable and surfaced on a close dashboard with ownership, ETA, and escalation policy.

### 4) Failure Handling and Operational Recovery
- Posting pipeline uses outbox/inbox patterns with deterministic retries and dead-letter quarantine for non-retriable payloads.
- Duplicate delivery and partial failure scenarios must be proven safe through idempotency and compensating accounting entries.
- Incident runbooks require: containment decision, scope quantification, replay/rebuild method, reconciliation rerun, and financial controller approval.
- Recovery drills must be executed periodically with evidence retained for audit.

### 5) Regulatory / Compliance / Audit Expectations
- Controls must support segregation of duties, least privilege, and end-to-end tamper-evident audit trails.
- Retention strategy must satisfy jurisdictional requirements for financial records, tax documents, and payroll artifacts.
- Sensitive data handling includes classification, masking/tokenization for non-production, and secure export controls.
- Every policy override (manual journal, reopened period, emergency access) requires reason code, approver, and expiration window.

### 6) Data Lineage & Traceability (Requirements → Implementation)
- Maintain an explicit traceability matrix for this artifact (`infrastructure/deployment-diagram.md`):
  - `Requirement ID` → `Business Rule / Event` → `Design Element` (API/schema/diagram component) → `Code Module` → `Test Evidence` → `Control Owner`.
- Lineage metadata minimums: source event ID, transformation ID/version, posting rule version, reconciliation batch ID, and report consumption path.
- Any change touching accounting semantics must include impact analysis across upstream requirements and downstream close/compliance reports.
- Documentation updates are blocking for release when they alter financial behavior, posting logic, or reconciliation outcomes.

### 7) Phase-Specific Implementation Readiness
- Enforce encryption in transit/at rest for PII/financial records and maintain key-rotation evidence.
- Provision isolated environments with masked production-like data and immutable audit-log sinks.
- Define RPO/RTO targets by finance process (payments, payroll, posting, close, reporting) and align backup strategy.

### 8) Implementation Checklist for `deployment diagram`
- [ ] Control objectives and success/failure criteria are explicit and testable.
- [ ] Data contracts include mandatory identifiers, timestamps, and provenance fields.
- [ ] Reconciliation logic defines cadence, tolerances, ownership, and escalation.
- [ ] Operational runbooks cover retries, replay, backfill, and close re-certification.
- [ ] Compliance evidence artifacts are named, retained, and linked to control owners.


### Mermaid Control Overlay (Implementation-Ready)
```mermaid
flowchart LR
    Req[Requirements Controls] --> Rules[Posting/Tax/Approval Rules]
    Rules --> Events[Domain Events with Idempotency Keys]
    Events --> Ledger[Immutable Ledger Entries]
    Ledger --> Recon[Automated Reconciliation Jobs]
    Recon --> Close[Period Close & Certification]
    Close --> Reports[Regulatory + Management Reports]
    Reports --> Audit[Evidence Store / Audit Trail]
    Audit -->|Feedback| Req
```


