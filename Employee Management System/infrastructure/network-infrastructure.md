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
