# Network Infrastructure

## Overview
Network topology and security architecture for the rental management system running on AWS.

---

## VPC Network Topology

```mermaid
graph TB
    subgraph "Internet"
        Users[Users & Clients]
        ExternalSvc[External Services<br>Stripe, DocuSign, Onfido, etc.]
    end

    subgraph "AWS - Primary Region (us-east-1)"
        subgraph "VPC: 10.0.0.0/16"
            subgraph "Public Subnets"
                PubA["Public Subnet AZ-A<br>10.0.1.0/24<br>ALB, NAT Gateway"]
                PubB["Public Subnet AZ-B<br>10.0.2.0/24<br>ALB, NAT Gateway"]
            end

            subgraph "Private App Subnets"
                PrivAppA["Private App Subnet AZ-A<br>10.0.11.0/24<br>EKS Nodes, Worker Nodes"]
                PrivAppB["Private App Subnet AZ-B<br>10.0.12.0/24<br>EKS Nodes, Worker Nodes"]
            end

            subgraph "Private Data Subnets"
                PrivDataA["Private Data Subnet AZ-A<br>10.0.21.0/24<br>RDS Primary, ElastiCache"]
                PrivDataB["Private Data Subnet AZ-B<br>10.0.22.0/24<br>RDS Standby, ElastiCache"]
            end

            IGW[Internet Gateway]
            NATGW_A[NAT Gateway AZ-A]
            NATGW_B[NAT Gateway AZ-B]
        end

        S3[S3 VPC Endpoint]
        SecretsManager[Secrets Manager VPC Endpoint]
    end

    Users --> IGW
    IGW --> PubA
    IGW --> PubB

    PubA --> NATGW_A
    PubB --> NATGW_B

    NATGW_A --> PrivAppA
    NATGW_B --> PrivAppB

    PrivAppA --> PrivDataA
    PrivAppB --> PrivDataB

    PrivAppA --> S3
    PrivAppB --> S3
    PrivAppA --> SecretsManager
    PrivAppB --> SecretsManager

    PrivAppA -.->|egress via NAT| ExternalSvc
    PrivAppB -.->|egress via NAT| ExternalSvc
```

---

## Security Group Configuration

```mermaid
graph TB
    subgraph "Security Groups"
        SG_ALB["ALB Security Group<br>Ingress: 80, 443 from 0.0.0.0/0<br>Egress: 3000 to App SG"]

        SG_App["App Security Group<br>Ingress: 3000 from ALB SG only<br>Egress: 5432 to DB SG, 6379 to Cache SG<br>Egress: 443 to 0.0.0.0/0 (external APIs)"]

        SG_DB["Database Security Group<br>Ingress: 5432 from App SG only<br>No public inbound"]

        SG_Cache["Cache Security Group<br>Ingress: 6379 from App SG only<br>No public inbound"]

        SG_Worker["Worker Security Group<br>Ingress: none<br>Egress: 5432 to DB SG, 6379 to Cache SG<br>Egress: 443 to 0.0.0.0/0"]
    end

    SG_ALB -->|"allow 3000"| SG_App
    SG_App -->|"allow 5432"| SG_DB
    SG_App -->|"allow 6379"| SG_Cache
    SG_Worker -->|"allow 5432"| SG_DB
    SG_Worker -->|"allow 6379"| SG_Cache
```

---

## CDN and Edge Configuration

```mermaid
graph LR
    Users[Users] --> CloudFront[CloudFront CDN]

    subgraph "CloudFront Behaviours"
        Static["/static/*<br>S3 Origin<br>Cache: 1 year"]
        API["/api/*<br>ALB Origin<br>Cache: none"]
        Media["/media/*<br>S3 Origin<br>Cache: 30 days"]
    end

    CloudFront --> Static
    CloudFront --> API
    CloudFront --> Media

    Static --> S3[S3 Static Assets]
    API --> WAF[AWS WAF]
    WAF --> ALB[Application Load Balancer]
    Media --> S3Media[S3 Media Bucket]
```

---

## WAF Rules Configuration

| Rule Group | Rules | Action |
|------------|-------|--------|
| AWS Managed Core Rules | SQL injection, XSS, known bad inputs | Block |
| Rate Limiting | > 1000 req/min per IP to `/api/*` | Block |
| Geographic Restriction | Block specific country codes if required | Block |
| Bot Control | Automated bot traffic detection | Count / Block |
| Custom: Auth Brute Force | > 10 failed `/auth/login` per IP per minute | Block for 10 min |
| Custom: Webhook Allowlist | `/webhooks/*` allowed only from known provider IPs | Allow / Block others |

---

## DNS Architecture

```mermaid
graph TB
    Domain["rental-platform.com"] --> Route53[Route 53 Hosted Zone]

    subgraph "DNS Records"
        RecordA["A / ALIAS<br>rental-platform.com → CloudFront"]
        RecordAPI["A / ALIAS<br>api.rental-platform.com → ALB"]
        RecordAssets["CNAME<br>assets.rental-platform.com → CloudFront"]
        RecordWS["A / ALIAS<br>ws.rental-platform.com → ALB"]
        RecordHealth["A<br>health.rental-platform.com → Internal ALB"]
    end

    Route53 --> RecordA
    Route53 --> RecordAPI
    Route53 --> RecordAssets
    Route53 --> RecordWS
    Route53 --> RecordHealth
```

---

## Certificate Management

| Domain | Certificate | Renewal |
|--------|-------------|---------|
| `rental-platform.com` | AWS ACM (wildcard `*.rental-platform.com`) | Auto-renew |
| `api.rental-platform.com` | AWS ACM | Auto-renew |
| `assets.rental-platform.com` | AWS ACM | Auto-renew |
| Internal services | Cert-Manager (Let's Encrypt) in EKS | Auto-renew |

---

## Port Reference

| Service | Port | Protocol | Accessible From |
|---------|------|----------|-----------------|
| ALB HTTPS | 443 | TCP | Internet (via WAF) |
| ALB HTTP | 80 | TCP | Internet (redirect to 443) |
| API App | 3000 | TCP | ALB SG only |
| WebSocket | 3001 | TCP | ALB SG only |
| PostgreSQL | 5432 | TCP | App SG, Worker SG only |
| Redis | 6379 | TCP | App SG, Worker SG only |
