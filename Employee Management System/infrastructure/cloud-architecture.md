# Cloud Architecture Diagram

## Overview
Cloud architecture diagram for the Employee Management System on AWS, showing managed services, regions, and service integrations.

---

## AWS Cloud Architecture

```mermaid
graph TB
    subgraph "Users"
        Employees[Employees\nWeb + Mobile]
        HRAdmin[HR / Admin\nWeb Portal]
        Biometric[Biometric Devices]
    end

    subgraph "AWS Cloud"
        subgraph "Edge Services"
            Route53[Route 53\nDNS + Health Routing]
            CloudFront[CloudFront CDN\nWeb + Assets]
            WAF[AWS WAF + Shield\nSecurity]
            ACM[Certificate Manager\nSSL/TLS]
        end

        subgraph "Compute - EKS"
            EKS[EKS Cluster\nKubernetes]
            API[API Service\nFastAPI / Node.js]
            Workers[Async Workers\nCelery / BullMQ]
            WS[WebSocket Service]
        end

        subgraph "Database - RDS"
            RDS[RDS PostgreSQL\nMulti-AZ]
            RDS_Replica[Read Replica\nReporting]
        end

        subgraph "Caching"
            ElastiCache[ElastiCache Redis\nCluster Mode]
        end

        subgraph "Async Processing"
            SQS[SQS Queues\nPayroll, Notifications, Reports]
            EventBridge[EventBridge\nScheduled payroll cycles]
        end

        subgraph "Storage"
            S3_Docs[S3 - Documents\nEmployee & Policy Docs]
            S3_Payslips[S3 - Payslips\nEncrypted Payslips]
            S3_Reports[S3 - Reports\nGenerated Report Artifacts]
            S3_Static[S3 - Static Assets\nFrontend Build]
        end

        subgraph "Communication"
            SES[SES\nTransactional Email]
            SNS[SNS\nSMS + Push Notifications]
            Pinpoint[Amazon Pinpoint\nMobile Push]
        end

        subgraph "Security"
            IAM_AWS[IAM Roles & Policies\nService Identity]
            SecretsManager[Secrets Manager\nAPI Keys + DB Creds]
            KMS[KMS\nEncryption Key Management]
            Cognito[Cognito\nExternal SSO Integration]
        end

        subgraph "Observability"
            CloudWatch[CloudWatch\nLogs + Metrics + Alarms]
            XRay[X-Ray\nDistributed Tracing]
            SecurityHub[Security Hub\nCompliance + Alerts]
            Config[AWS Config\nInfrastructure Compliance]
        end
    end

    subgraph "External"
        ERPSystem[ERP / Accounting System]
        BankingAPI[Banking / Salary Disbursement]
        IdPSAML[Enterprise IdP\nSAML 2.0]
    end

    Employees --> Route53
    HRAdmin --> Route53
    Biometric -->|TLS| Route53

    Route53 --> CloudFront
    CloudFront --> WAF
    WAF --> EKS
    ACM --> CloudFront

    EKS --> API
    EKS --> Workers
    EKS --> WS

    API --> RDS
    API --> RDS_Replica
    API --> ElastiCache
    API --> SQS
    API --> S3_Docs
    API --> S3_Payslips
    API --> SecretsManager

    Workers --> SQS
    Workers --> RDS
    Workers --> SES
    Workers --> SNS
    Workers --> Pinpoint
    Workers --> BankingAPI
    Workers --> S3_Reports

    SQS --> Workers
    EventBridge --> SQS

    S3_Static --> CloudFront

    API --> CloudWatch
    API --> XRay
    Workers --> CloudWatch

    API <--> ERPSystem
    API <--> IdPSAML
    API --> Cognito

    KMS --> S3_Docs
    KMS --> S3_Payslips
    KMS --> RDS

    CloudWatch --> SecurityHub
    Config --> SecurityHub
```

---

## Multi-Environment Setup

| Environment | Purpose | Scale | Notes |
|-------------|---------|-------|-------|
| **Development** | Developer testing | Minimal (single pod) | Shared DB, no HA |
| **Staging** | Pre-production testing | Reduced (2 pods) | Mirrors production config |
| **Production** | Live system | Full HA (3+ pods) | Multi-AZ, DR enabled |
| **DR (Disaster Recovery)** | Failover | Standby (warm) | Cross-region replica |

---

## Cost Optimization Strategies

| Strategy | Implementation |
|----------|---------------|
| **Reserved Instances** | RDS and ElastiCache 1-year reservations for predictable workloads |
| **Spot Workers** | Async workers run on Spot instances with graceful termination handling |
| **S3 Lifecycle Policies** | Archive payslips older than 2 years to S3 Glacier |
| **CloudFront Caching** | Cache static assets aggressively; API responses with short TTLs |
| **Auto-Scaling** | HPA on CPU/memory for API pods; queue-depth scaling for workers |
| **Right-Sizing** | Periodic review of instance types based on CloudWatch metrics |

---

---

## Process Narrative (Cloud foundation architecture)
1. **Initiate**: Cloud Architect captures the primary change request for **Cloud Architecture** and links it to business objectives, impacted modules, and target release windows.
2. **Design/Refine**: The team elaborates flows, assumptions, acceptance criteria, and exception paths specific to cloud foundation architecture.
3. **Authorize**: Approval checks confirm that changes satisfy policy, architecture, and compliance constraints before promotion.
4. **Execute**: IaC Pipeline executes the approved path and enforces infra policy checks at run-time or publication-time.
5. **Integrate**: Outputs are synchronized to dependent services (IAM, payroll, reporting, notifications, and audit store) with idempotent correlation IDs.
6. **Verify & Close**: Stakeholders reconcile expected outcomes against actual telemetry to confirm platform reliability.

## Role/Permission Matrix (Cloud Architecture)
| Capability | Employee | Manager | HR/People Ops | Engineering/IT | Compliance/Audit |
|---|---|---|---|---|---|
| View cloud architecture artifacts | Scoped self | Team scoped | Full | Full | Read-only full |
| Propose change | Request only | Draft + justify | Draft + justify | Draft + justify | No |
| Approve publication/use | No | Conditional | Primary approver | Technical approver | Control sign-off |
| Execute override | No | Limited with reason | Limited with reason | Break-glass with ticket | No |
| Access evidence trail | No | Limited | Full | Full | Full |

## State Model (Cloud foundation architecture)
```mermaid
stateDiagram-v2
    [*] --> Draft
    Draft --> InReview: submit
    InReview --> Approved: functional + technical checks
    InReview --> Rework: feedback
    Rework --> InReview: resubmit
    Approved --> Released: publish/deploy
    Released --> Monitored: telemetry active
    Monitored --> Stable: controls pass
    Monitored --> Incident: control failure
    Incident --> Rework: corrective action
    Stable --> [*]
```

## Integration Behavior (Cloud Architecture)
| Integration | Trigger | Expected Behavior | Failure Handling |
|---|---|---|---|
| IAM / RBAC | Approval or assignment change | Sync permission scopes for affected actors | Retry + alert on drift |
| Workflow/Event Bus | State transition | Publish canonical event with correlation ID | Dead-letter + replay tooling |
| Payroll/Benefits (where applicable) | Compensation/lifecycle change | Apply financial side-effects only after approved state | Hold payout + reconcile |
| Notification Channels | Review decision, exception, due date | Deliver actionable notice to owners and requestors | Escalation after SLA breach |
| Audit/GRC Archive | Any controlled transition | Store immutable evidence bundle | Block progression if evidence missing |

## Onboarding/Offboarding Edge Cases (Concrete)
- **Rehire with residual access**: If a rehire request reuses a prior identity, retain historical employee ID linkage but force fresh role entitlement approval before day-1 access.
- **Early start-date acceleration**: When onboarding date is moved earlier than background-check SLA, block activation and auto-create an exception approval task.
- **Same-day termination**: For involuntary offboarding, revoke privileged access immediately while preserving records under legal hold classification.
- **Rescinded resignation after downstream sync**: If offboarding is canceled after payroll/IAM notifications, execute compensating events and log full reversal trail.

## Compliance/Audit Controls
| Control | Description | Evidence |
|---|---|---|
| Segregation of duties | Requestor and approver cannot be the same identity for controlled actions | Approval chain + user IDs |
| Transition integrity | Only allowed state transitions can be persisted | Transition log + rejection reasons |
| Timely deprovisioning | Offboarding access revocation meets SLA targets | IAM revocation timestamp report |
| Financial reconciliation | Payroll-impacting changes reconcile before close | Payroll batch diff + sign-off |
| Immutable auditability | Controlled actions are archived in WORM/append-only storage | Hash, retention tag, archive pointer |

