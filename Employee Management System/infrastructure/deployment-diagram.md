# Deployment Diagram

## Overview
Deployment diagrams showing the mapping of software components to hardware and infrastructure for the Employee Management System.

---

## Production Deployment Architecture

```mermaid
graph TB
    subgraph "Internet"
        Users[Users / Clients]
        BiometricDevices[Biometric Devices]
    end

    subgraph "Edge Layer"
        DNS[Route 53 DNS]
        CloudFront[CloudFront CDN\nStatic Assets]
        WAF[AWS WAF\nDDoS, OWASP protection]
    end

    subgraph "AWS Region - Primary"
        subgraph "VPC - Production"
            subgraph "Public Subnet AZ-A"
                ALB_A[Application Load Balancer]
                NAT_A[NAT Gateway]
            end

            subgraph "Public Subnet AZ-B"
                ALB_B[Application Load Balancer]
                NAT_B[NAT Gateway]
            end

            subgraph "Private Subnet AZ-A - Application"
                EKS_A[EKS Worker Nodes\nAPI Service Pods]
                Worker_A[EKS Worker Nodes\nAsync Worker Pods]
            end

            subgraph "Private Subnet AZ-B - Application"
                EKS_B[EKS Worker Nodes\nAPI Service Pods]
                Worker_B[EKS Worker Nodes\nAsync Worker Pods]
            end

            subgraph "Private Subnet AZ-A - Data"
                RDS_Primary[(RDS PostgreSQL\nPrimary)]
                ElastiCache_A[(ElastiCache Redis\nAZ-A)]
            end

            subgraph "Private Subnet AZ-B - Data"
                RDS_Standby[(RDS PostgreSQL\nStandby)]
                ElastiCache_B[(ElastiCache Redis\nAZ-B)]
            end
        end

        EKS_Control[EKS Control Plane\nAWS Managed]
        S3[S3 Buckets\nDocuments, Payslips, Reports]
        SQS[Amazon SQS\nTask Queue]
        SES[Amazon SES\nEmail Service]
        SNS[Amazon SNS\nSMS & Push]
    end

    subgraph "AWS Region - DR"
        RDS_DR[(RDS Read Replica\nDR Region)]
        S3_DR[S3 Replication]
    end

    Users --> DNS
    DNS --> CloudFront
    CloudFront --> WAF
    WAF --> ALB_A
    WAF --> ALB_B

    ALB_A --> EKS_A
    ALB_B --> EKS_B

    EKS_A --> RDS_Primary
    EKS_B --> RDS_Primary
    EKS_A --> ElastiCache_A
    EKS_B --> ElastiCache_B

    EKS_A --> SQS
    EKS_B --> SQS
    SQS --> Worker_A
    SQS --> Worker_B

    Worker_A --> SES
    Worker_B --> SNS
    Worker_A --> S3

    EKS_A --> S3
    EKS_B --> S3

    RDS_Primary --> RDS_Standby
    RDS_Primary --> RDS_DR
    S3 --> S3_DR

    BiometricDevices -->|TLS| ALB_A
```

---

## Kubernetes Pod Layout

```mermaid
graph TB
    subgraph "Kubernetes Cluster"
        subgraph "Namespace: ems-production"
            subgraph "API Deployment"
                API_Pod1[API Pod 1\nFastAPI / Node.js]
                API_Pod2[API Pod 2]
                API_Pod3[API Pod 3]
            end

            subgraph "Worker Deployment"
                Worker_Pod1[Worker Pod 1\nPayroll Processing]
                Worker_Pod2[Worker Pod 2\nReport Generation]
                Worker_Pod3[Worker Pod 3\nNotification Delivery]
            end

            subgraph "WebSocket Deployment"
                WS_Pod1[WebSocket Pod 1]
                WS_Pod2[WebSocket Pod 2]
            end

            subgraph "Config & Secrets"
                ConfigMap[ConfigMap\nApp Settings]
                Secrets[Secrets\nDB Creds, API Keys]
            end

            HPA_API[HPA - API\nCPU/Memory based]
            HPA_Worker[HPA - Worker\nQueue depth based]
        end
    end

    IngressController[NGINX Ingress Controller] --> API_Pod1
    IngressController --> API_Pod2
    IngressController --> API_Pod3
    IngressController --> WS_Pod1
    IngressController --> WS_Pod2

    API_Pod1 --> ConfigMap
    API_Pod1 --> Secrets
    Worker_Pod1 --> Secrets

    HPA_API --> API_Pod1
    HPA_Worker --> Worker_Pod1
```

---

## CI/CD Pipeline

```mermaid
graph LR
    Dev[Developer Push] --> GitRepo[Git Repository]
    GitRepo --> CI[CI Pipeline\nGitHub Actions / GitLab CI]
    CI --> Lint[Lint & Format Check]
    Lint --> Tests[Unit & Integration Tests]
    Tests --> Build[Docker Build]
    Build --> SAST[SAST Security Scan]
    SAST --> Registry[Container Registry\nECR / DockerHub]
    Registry --> StagingDeploy[Deploy to Staging]
    StagingDeploy --> E2E[E2E Tests]
    E2E --> ManualApproval{Manual Approval}
    ManualApproval --> ProdDeploy[Deploy to Production\nRolling Update]
    ProdDeploy --> HealthCheck[Health Check\nReadiness Probe]
    HealthCheck --> Done([Deployment Complete])
```

---

---

## Process Narrative (Deployment topology)
1. **Initiate**: Release Manager captures the primary change request for **Deployment Diagram** and links it to business objectives, impacted modules, and target release windows.
2. **Design/Refine**: The team elaborates flows, assumptions, acceptance criteria, and exception paths specific to deployment topology.
3. **Authorize**: Approval checks confirm that changes satisfy policy, architecture, and compliance constraints before promotion.
4. **Execute**: Deployment Controller executes the approved path and enforces promotion gate checks at run-time or publication-time.
5. **Integrate**: Outputs are synchronized to dependent services (IAM, payroll, reporting, notifications, and audit store) with idempotent correlation IDs.
6. **Verify & Close**: Stakeholders reconcile expected outcomes against actual telemetry to confirm release safety.

## Role/Permission Matrix (Deployment Diagram)
| Capability | Employee | Manager | HR/People Ops | Engineering/IT | Compliance/Audit |
|---|---|---|---|---|---|
| View deployment diagram artifacts | Scoped self | Team scoped | Full | Full | Read-only full |
| Propose change | Request only | Draft + justify | Draft + justify | Draft + justify | No |
| Approve publication/use | No | Conditional | Primary approver | Technical approver | Control sign-off |
| Execute override | No | Limited with reason | Limited with reason | Break-glass with ticket | No |
| Access evidence trail | No | Limited | Full | Full | Full |

## State Model (Deployment topology)
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

## Integration Behavior (Deployment Diagram)
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

