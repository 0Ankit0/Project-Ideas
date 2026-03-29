# Network / Infrastructure Diagram

## Overview
Network and infrastructure diagrams for the Employee Management System, showing security zones, traffic flow, and internal connectivity.

---

## Network Architecture

```mermaid
graph TB
    subgraph "Internet Zone"
        Internet[Internet]
        BiometricVPN[Biometric Devices\nSite-to-Site VPN / TLS]
        ERPLink[ERP System\nPrivate Link / VPN]
    end

    subgraph "Edge / DMZ Zone"
        CloudFront[CloudFront CDN\n- Static assets\n- DDoS mitigation]
        WAF[Web Application Firewall\n- OWASP rules\n- IP allowlisting for biometric]
        ALB[Application Load Balancer\n- SSL termination\n- Health-based routing]
    end

    subgraph "Application Zone - Private Subnet"
        API[API Service Cluster\nHorizontally scaled pods]
        Workers[Async Worker Cluster\nPayroll + Notification workers]
        WS[WebSocket Service]
        Cache[Redis Cluster\nSessions + Balances]
    end

    subgraph "Data Zone - Isolated Subnet"
        DB_Primary[(PostgreSQL Primary\nMulti-AZ)]
        DB_Replica[(PostgreSQL Read Replica\nReporting queries)]
        Storage[(S3 Object Storage\nEncrypted at rest)]
    end

    subgraph "Monitoring Zone"
        Prometheus[Prometheus\nMetrics collection]
        Grafana[Grafana\nDashboards]
        Loki[Loki\nLog aggregation]
        Alertmanager[Alertmanager\nOn-call alerts]
    end

    subgraph "External Services Zone"
        Email[Email SES]
        SMS[SMS SNS]
        Bank[Banking API\nTLS mutual auth]
        IdP[Identity Provider SSO]
    end

    Internet --> CloudFront
    CloudFront --> WAF
    WAF --> ALB
    ALB --> API
    ALB --> WS

    BiometricVPN -->|VPN / TLS| WAF
    ERPLink -->|Private Link| API

    API --> Cache
    API --> DB_Primary
    API --> Storage
    API --> Workers

    Workers --> DB_Primary
    Workers --> Storage
    Workers --> Email
    Workers --> SMS
    Workers --> Bank

    DB_Primary --> DB_Replica
    API --> DB_Replica

    API --> Prometheus
    Workers --> Prometheus
    Prometheus --> Grafana
    Prometheus --> Alertmanager
    API --> Loki

    API <--> IdP
```

---

## Security Architecture

```mermaid
graph TB
    subgraph "Perimeter Security"
        WAF[Web Application Firewall\nOWASP Top 10 rules]
        DDoS[DDoS Protection\nCloudFront Shield]
        RateLimit[API Rate Limiting\nPer-user and global]
    end

    subgraph "Identity & Access"
        JWT[JWT Authentication\nRS256 signed tokens]
        RBAC[Role-Based Access Control\nModule-level enforcement]
        MFA[Multi-Factor Auth\n2FA for privileged roles]
        SSO[Enterprise SSO\nSAML 2.0 / OAuth 2.0]
    end

    subgraph "Data Security"
        TLS[TLS 1.3\nAll transport]
        EncryptRest[AES-256 Encryption\nPII and payroll data at rest]
        EncryptStorage[S3 SSE-KMS\nDocuments and payslips]
        DBEncrypt[RDS Encryption\nPostgres TDE]
    end

    subgraph "Operational Security"
        AuditLog[Audit Logging\nAll write operations]
        SIEM[SIEM Integration\nCloudWatch + Security Hub]
        SecretsMgmt[Secrets Manager\nAWS Secrets Manager]
        VulnScan[Vulnerability Scanning\nECR image scan on push]
    end

    subgraph "Compliance Controls"
        GDPR[GDPR Controls\nData retention and deletion]
        DataResidency[Data Residency\nRegion-pinned storage]
        BackupPolicy[Backup Policy\nDaily full, hourly incremental]
    end
```

---

## High Availability Topology

```mermaid
graph LR
    subgraph "AZ-A"
        ALB_A[Load Balancer A]
        API_A[API Pods A]
        Worker_A[Worker Pods A]
        Redis_A[(Redis A)]
        RDS_Primary[(RDS Primary)]
    end

    subgraph "AZ-B"
        ALB_B[Load Balancer B]
        API_B[API Pods B]
        Worker_B[Worker Pods B]
        Redis_B[(Redis B)]
        RDS_Standby[(RDS Standby)]
    end

    Route53[Route 53\nActive-Active DNS] --> ALB_A
    Route53 --> ALB_B

    ALB_A --> API_A
    ALB_B --> API_B

    API_A --> Redis_A
    API_B --> Redis_B
    Redis_A <--> Redis_B

    API_A --> RDS_Primary
    API_B --> RDS_Primary
    RDS_Primary --> RDS_Standby

    Worker_A --> RDS_Primary
    Worker_B --> RDS_Primary
```

---

---

## Process Narrative (Network segmentation model)
1. **Initiate**: Network Architect captures the primary change request for **Network Infrastructure** and links it to business objectives, impacted modules, and target release windows.
2. **Design/Refine**: The team elaborates flows, assumptions, acceptance criteria, and exception paths specific to network segmentation model.
3. **Authorize**: Approval checks confirm that changes satisfy policy, architecture, and compliance constraints before promotion.
4. **Execute**: Network Controller executes the approved path and enforces traffic policy checks at run-time or publication-time.
5. **Integrate**: Outputs are synchronized to dependent services (IAM, payroll, reporting, notifications, and audit store) with idempotent correlation IDs.
6. **Verify & Close**: Stakeholders reconcile expected outcomes against actual telemetry to confirm connectivity assurance.

## Role/Permission Matrix (Network Infrastructure)
| Capability | Employee | Manager | HR/People Ops | Engineering/IT | Compliance/Audit |
|---|---|---|---|---|---|
| View network infrastructure artifacts | Scoped self | Team scoped | Full | Full | Read-only full |
| Propose change | Request only | Draft + justify | Draft + justify | Draft + justify | No |
| Approve publication/use | No | Conditional | Primary approver | Technical approver | Control sign-off |
| Execute override | No | Limited with reason | Limited with reason | Break-glass with ticket | No |
| Access evidence trail | No | Limited | Full | Full | Full |

## State Model (Network segmentation model)
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

## Integration Behavior (Network Infrastructure)
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

