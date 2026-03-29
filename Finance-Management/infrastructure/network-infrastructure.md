# Network Infrastructure

## Overview
Network topology and security architecture for the Finance Management System, designed with defense-in-depth and zero-trust principles suitable for a financial application.

---

## VPC Network Architecture

```mermaid
graph TB
    subgraph "Internet"
        Internet[Internet]
    end

    subgraph "AWS Edge Services"
        R53[Route 53<br>DNS]
        CF[CloudFront<br>CDN]
        WAF[AWS WAF]
        Shield[Shield Advanced]
    end

    subgraph "VPC (10.0.0.0/16)"
        subgraph "Public Subnets"
            subgraph "AZ-a (10.0.1.0/24)"
                ALB_a[ALB Node]
                NAT_a[NAT Gateway]
            end
            subgraph "AZ-b (10.0.2.0/24)"
                ALB_b[ALB Node]
                NAT_b[NAT Gateway]
            end
        end

        subgraph "Private App Subnets"
            subgraph "AZ-a (10.0.10.0/24)"
                EKS_a[EKS Nodes<br>Finance API + Workers]
            end
            subgraph "AZ-b (10.0.11.0/24)"
                EKS_b[EKS Nodes<br>Finance API + Workers]
            end
        end

        subgraph "Private Data Subnets"
            subgraph "AZ-a (10.0.20.0/24)"
                RDS_a[RDS Primary]
                Redis_a[ElastiCache Node]
            end
            subgraph "AZ-b (10.0.21.0/24)"
                RDS_b[RDS Standby / Replica]
                Redis_b[ElastiCache Node]
            end
        end

        subgraph "VPC Endpoints (PrivateLink)"
            EP_S3[S3 Gateway Endpoint]
            EP_SQS[SQS Interface Endpoint]
            EP_SM[Secrets Manager Endpoint]
            EP_KMS[KMS Endpoint]
            EP_ECR[ECR Interface Endpoint]
            EP_CW[CloudWatch Endpoint]
        end
    end

    subgraph "External Services (via NAT)"
        BankAPI[Banking APIs<br>ACH / SWIFT]
        TaxPortal[Tax Authority Portal]
        FXFeed[FX Rate Feed]
    end

    Internet --> R53
    R53 --> CF
    CF --> Shield
    Shield --> WAF
    WAF --> ALB_a
    WAF --> ALB_b

    ALB_a --> EKS_a
    ALB_b --> EKS_b

    EKS_a --> RDS_a
    EKS_a --> Redis_a
    EKS_b --> RDS_b
    EKS_b --> Redis_b

    EKS_a --> EP_S3
    EKS_a --> EP_SQS
    EKS_a --> EP_SM
    EKS_a --> EP_KMS
    EKS_a --> EP_ECR
    EKS_a --> EP_CW

    EKS_a --> NAT_a
    NAT_a --> BankAPI
    NAT_a --> TaxPortal
    NAT_a --> FXFeed
```

---

## Security Group Rules

```mermaid
graph LR
    subgraph "Security Groups"
        ALB_SG["ALB-SG\nInbound: 443 from 0.0.0.0/0\nOutbound: 8000 to App-SG"]

        App_SG["App-SG\nInbound: 8000 from ALB-SG\nInbound: 8000 from App-SG (inter-pod)\nOutbound: 5432 to Data-SG\nOutbound: 6379 to Data-SG\nOutbound: 443 to VPC Endpoints"]

        Worker_SG["Worker-SG\nInbound: none\nOutbound: 5432 to Data-SG\nOutbound: 443 to VPC Endpoints\nOutbound: 443 to NAT (bank/tax)"]

        Data_SG["Data-SG\nInbound: 5432 from App-SG\nInbound: 5432 from Worker-SG\nInbound: 6379 from App-SG\nOutbound: none"]

        Bastion_SG["Bastion-SG (Admin Access)\nInbound: 22 from VPN CIDR only\nOutbound: 22 to Data-SG\nOutbound: 5432 to Data-SG"]
    end

    ALB_SG --> App_SG
    App_SG --> Data_SG
    Worker_SG --> Data_SG
    Bastion_SG --> Data_SG
```

---

## Network Traffic Flow

```mermaid
sequenceDiagram
    participant User as Finance User
    participant DNS as Route 53
    participant CDN as CloudFront
    participant WAF as AWS WAF
    participant ALB as Load Balancer
    participant API as Finance API (EKS)
    participant DB as RDS PostgreSQL
    participant Audit as Audit Log DB
    participant Bank as Banking API (External)

    User->>DNS: DNS Query finance.company.com
    DNS-->>User: ALB IP via CloudFront

    User->>CDN: HTTPS Request
    CDN->>WAF: Forward Request
    WAF->>WAF: Inspect (OWASP rules, rate limit)
    WAF->>ALB: Forward if clean
    ALB->>API: HTTPS to EKS Pod (TLS termination at ALB)

    API->>DB: SQL Query (private subnet, SG-restricted)
    DB-->>API: Query Result

    API->>Audit: Write audit log (INSERT only role)
    Audit-->>API: Logged

    alt Payment Run Submission
        API->>Bank: HTTPS POST (via NAT Gateway, mTLS)
        Bank-->>API: ACH Accepted
    end

    API-->>ALB: HTTP Response
    ALB-->>CDN: Response
    CDN-->>User: Final Response
```

---

## Multi-AZ Failover Architecture

```mermaid
graph TB
    subgraph "Normal Operation"
        ALB_Normal[ALB - Both AZs Active]
        EKS_A[EKS AZ-a<br>Primary pods]
        EKS_B[EKS AZ-b<br>Secondary pods]
        RDS_Primary[(RDS Primary<br>AZ-a)]
        RDS_Standby[(RDS Standby<br>AZ-b)]
    end

    subgraph "AZ-a Failure Scenario"
        ALB_Fail[ALB - Routes to AZ-b only]
        EKS_B_Fail[EKS AZ-b<br>Handles all traffic<br>HPA scales up]
        RDS_Failover[(RDS Auto-Failover<br>Standby → Primary<br>~30 seconds)]
    end

    ALB_Normal --> EKS_A
    ALB_Normal --> EKS_B
    EKS_A --> RDS_Primary
    EKS_B --> RDS_Primary
    RDS_Primary -.->|Sync Replication| RDS_Standby

    ALB_Fail --> EKS_B_Fail
    EKS_B_Fail --> RDS_Failover
```

---

## Network Access Control Summary

| Layer | Control | Implementation |
|-------|---------|---------------|
| Internet edge | DDoS protection | AWS Shield Advanced |
| Internet edge | Web application firewall | AWS WAF with OWASP + custom finance rules |
| DNS | Health-check-based routing | Route 53 health checks |
| Load balancer | TLS termination, HTTP → HTTPS redirect | ALB with ACM certificate |
| VPC | Network segmentation | Public, App, Data subnet tiers |
| Pods | Pod-to-pod restriction | Kubernetes NetworkPolicies |
| Security groups | Port-level access control | SG rules per tier as documented |
| Database | No direct internet access | Private subnets only |
| External API calls | Outbound via NAT with IP allowlisting | NAT Gateway + WAF egress rules |
| AWS services | No internet traversal | VPC PrivateLink / Gateway Endpoints |
| Secrets | No hardcoded credentials | AWS Secrets Manager + External Secrets Operator |
| Admin access | Bastion host with VPN requirement | VPN-only access to bastion SG |

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
- Maintain an explicit traceability matrix for this artifact (`infrastructure/network-infrastructure.md`):
  - `Requirement ID` → `Business Rule / Event` → `Design Element` (API/schema/diagram component) → `Code Module` → `Test Evidence` → `Control Owner`.
- Lineage metadata minimums: source event ID, transformation ID/version, posting rule version, reconciliation batch ID, and report consumption path.
- Any change touching accounting semantics must include impact analysis across upstream requirements and downstream close/compliance reports.
- Documentation updates are blocking for release when they alter financial behavior, posting logic, or reconciliation outcomes.

### 7) Phase-Specific Implementation Readiness
- Enforce encryption in transit/at rest for PII/financial records and maintain key-rotation evidence.
- Provision isolated environments with masked production-like data and immutable audit-log sinks.
- Define RPO/RTO targets by finance process (payments, payroll, posting, close, reporting) and align backup strategy.

### 8) Implementation Checklist for `network infrastructure`
- [ ] Control objectives and success/failure criteria are explicit and testable.
- [ ] Data contracts include mandatory identifiers, timestamps, and provenance fields.
- [ ] Reconciliation logic defines cadence, tolerances, ownership, and escalation.
- [ ] Operational runbooks cover retries, replay, backfill, and close re-certification.
- [ ] Compliance evidence artifacts are named, retained, and linked to control owners.


