# Network Infrastructure

## Overview
Network and infrastructure diagrams showing the network topology, security zones, and connectivity for the Student Information System.

---

## Network Topology Diagram

```mermaid
graph TB
    subgraph "Internet"
        Users[Users / Clients]
        ExternalSystems[External Systems<br>Payment Gateways / LDAP / Library]
    end

    subgraph "AWS Cloud"
        subgraph "Edge / Public Layer"
            Route53[Route 53<br>DNS Resolution]
            CloudFront[CloudFront<br>CDN + Static Assets]
            WAF[AWS WAF<br>DDoS / Bot Protection]
        end

        subgraph "VPC - 10.0.0.0/16"
            subgraph "Public Subnet A - 10.0.1.0/24"
                ALB_A[Application Load Balancer A]
                NAT_A[NAT Gateway A]
                BastionA[Bastion Host A]
            end

            subgraph "Public Subnet B - 10.0.2.0/24"
                ALB_B[Application Load Balancer B]
                NAT_B[NAT Gateway B]
            end

            subgraph "Private Subnet A - App - 10.0.11.0/24"
                EKS_A[EKS Nodes A<br>SIS Application Pods]
            end

            subgraph "Private Subnet B - App - 10.0.12.0/24"
                EKS_B[EKS Nodes B<br>SIS Application Pods]
            end

            subgraph "Private Subnet A - Data - 10.0.21.0/24"
                RDS_Primary[(RDS Primary<br>PostgreSQL)]
                Redis_A[(ElastiCache<br>Redis Cluster A)]
            end

            subgraph "Private Subnet B - Data - 10.0.22.0/24"
                RDS_Standby[(RDS Standby)]
                Redis_B[(ElastiCache<br>Redis Cluster B)]
            end

            SecurityGroup_App[Security Group: App<br>Allow 8000 from ALB]
            SecurityGroup_DB[Security Group: DB<br>Allow 5432 from App SG]
        end

        S3[S3 Bucket<br>Documents / Transcripts]
        SES[Amazon SES<br>Transactional Email]
        SNS[Amazon SNS<br>SMS Notifications]
    end

    Users --> Route53
    Route53 --> CloudFront
    CloudFront --> WAF
    WAF --> ALB_A
    WAF --> ALB_B

    ALB_A --> EKS_A
    ALB_B --> EKS_B

    EKS_A --> RDS_Primary
    EKS_B --> RDS_Primary
    EKS_A --> Redis_A
    EKS_B --> Redis_B

    EKS_A --> S3
    EKS_B --> S3
    EKS_A --> SES
    EKS_A --> SNS

    RDS_Primary -.->|Multi-AZ Standby| RDS_Standby
    Redis_A <-.->|Cluster Replication| Redis_B

    EKS_A --> NAT_A
    EKS_B --> NAT_B
    NAT_A --> ExternalSystems
    NAT_B --> ExternalSystems
```

---

## Security Group Rules

### Application Layer Security Group

| Rule | Protocol | Port | Source | Purpose |
|------|----------|------|--------|---------|
| Inbound | HTTPS | 443 | ALB Security Group | API traffic |
| Inbound | HTTP | 8000 | ALB Security Group | Internal API |
| Outbound | TCP | 5432 | DB Security Group | PostgreSQL |
| Outbound | TCP | 6379 | Cache Security Group | Redis |
| Outbound | HTTPS | 443 | 0.0.0.0/0 via NAT | External services |

### Database Layer Security Group

| Rule | Protocol | Port | Source | Purpose |
|------|----------|------|--------|---------|
| Inbound | TCP | 5432 | App Security Group | PostgreSQL connections |
| Outbound | None | - | - | No outbound required |

---

## DNS and Routing

```mermaid
graph LR
    subgraph "DNS Structure"
        Domain[college.edu]
        SIS[sis.college.edu<br>Student Portal]
        Faculty[faculty.college.edu<br>Faculty Portal]
        Admin[admin.college.edu<br>Admin Dashboard]
        API[api.college.edu<br>REST API]
        Parent[parent.college.edu<br>Parent Portal]
    end

    subgraph "CloudFront Distributions"
        CF_Student[Student CDN]
        CF_Faculty[Faculty CDN]
        CF_Admin[Admin CDN]
        CF_API[API CDN / Pass-through]
    end

    Domain --> SIS
    Domain --> Faculty
    Domain --> Admin
    Domain --> API
    Domain --> Parent

    SIS --> CF_Student
    Faculty --> CF_Faculty
    Admin --> CF_Admin
    API --> CF_API
    Parent --> CF_Student
```

---

## Internal Service Mesh

```mermaid
graph TB
    subgraph "Kubernetes Cluster"
        subgraph "Service Mesh (Istio)"
            IngressGW[Istio Ingress Gateway]

            subgraph "Services"
                AuthSvc[auth-service:8000]
                StudentSvc[student-service:8000]
                CourseSvc[course-service:8000]
                EnrollSvc[enrollment-service:8000]
                GradeSvc[grade-service:8000]
                AttendanceSvc[attendance-service:8000]
                FeeSvc[fee-service:8000]
                NotifSvc[notification-service:8000]
            end
        end

        subgraph "Config and Secrets"
            ConfigMap[ConfigMap<br>App Configuration]
            Secrets[Kubernetes Secrets<br>DB Creds, API Keys]
        end
    end

    IngressGW --> AuthSvc
    IngressGW --> StudentSvc
    IngressGW --> CourseSvc
    IngressGW --> EnrollSvc
    IngressGW --> GradeSvc
    IngressGW --> AttendanceSvc
    IngressGW --> FeeSvc

    EnrollSvc --> NotifSvc
    GradeSvc --> NotifSvc
    AttendanceSvc --> NotifSvc
    FeeSvc --> NotifSvc

    AuthSvc --> Secrets
    FeeSvc --> Secrets
    StudentSvc --> ConfigMap
```

---

## Monitoring and Observability

```mermaid
graph TB
    subgraph "Application"
        SISApp[SIS Application Pods]
    end

    subgraph "Observability Stack"
        Prometheus[Prometheus<br>Metrics Collection]
        Grafana[Grafana<br>Dashboards]
        Jaeger[Jaeger<br>Distributed Tracing]
        ELK[ELK Stack<br>Log Aggregation]
    end

    subgraph "Alerting"
        AlertManager[Alert Manager]
        PagerDuty[PagerDuty<br>On-call Alerts]
    end

    SISApp -->|Metrics| Prometheus
    SISApp -->|Traces| Jaeger
    SISApp -->|Logs| ELK

    Prometheus --> Grafana
    Prometheus --> AlertManager
    AlertManager --> PagerDuty

    Jaeger --> Grafana
    ELK --> Grafana
```

---

## Backup and Disaster Recovery

| Component | Backup Strategy | RPO | RTO |
|-----------|----------------|-----|-----|
| PostgreSQL | Hourly incremental + daily full; Multi-AZ standby | 1 hour | 30 minutes |
| Redis | Multi-node cluster; point-in-time snapshots | 15 minutes | 15 minutes |
| S3 (Documents) | Cross-region replication; versioning enabled | Near-zero | Near-zero |
| Application Config | Git-managed; ArgoCD reconciliation | Minutes | Minutes |
