# Network Infrastructure Diagram

## Overview
This document describes the network topology and security boundaries for the CMS platform deployment.

---

## Network Topology

```mermaid
graph TB
    Internet((Internet))

    subgraph "Edge / CDN"
        CDN[CDN<br>CloudFront / Fastly<br>Global PoPs]
        WAF[WAF<br>Rate limiting, IP blocking, OWASP rules]
    end

    subgraph "AWS / GCP Region"
        subgraph "Public Subnet"
            ALB[Application Load Balancer<br>HTTPS :443 only]
            NATGateway[NAT Gateway<br>Outbound only for private subnets]
        end

        subgraph "Private Subnet A — Application"
            APIPods[CMS API Pods<br>Port 8000 internal]
            WorkerPods[Background Worker Pods<br>No inbound]
            WSPods[WebSocket Pods<br>Port 8001 internal]
            FrontendPods[Public Frontend Pods<br>Port 3000 internal]
        end

        subgraph "Private Subnet B — Data"
            PGPrimary[(PostgreSQL Primary<br>Port 5432)]
            PGReplica[(PostgreSQL Replica<br>Port 5432 read-only)]
            Redis[(Redis Cluster<br>Port 6379)]
            Meilisearch[(Meilisearch<br>Port 7700)]
        end

        subgraph "Isolated Subnet — Admin"
            AdminPods[Admin SPA Pods<br>Port 80 internal]
        end
    end

    subgraph "External Services"
        EmailSvc[Email Provider<br>api.sendgrid.com :443]
        SpamSvc[Spam Filter API<br>:443]
        OAuthProvider[OAuth2 Provider<br>accounts.google.com :443]
        S3[Object Storage<br>s3.amazonaws.com :443]
    end

    Internet --> CDN
    CDN --> WAF
    WAF --> ALB

    ALB --> APIPods
    ALB --> FrontendPods
    ALB --> WSPods
    ALB --> AdminPods

    APIPods --> PGPrimary
    APIPods --> PGReplica
    APIPods --> Redis
    APIPods --> Meilisearch

    WorkerPods --> PGPrimary
    WorkerPods --> Redis
    WorkerPods --> NATGateway

    APIPods --> NATGateway

    NATGateway --> EmailSvc
    NATGateway --> SpamSvc
    NATGateway --> OAuthProvider
    NATGateway --> S3
```

---

## Security Groups / Firewall Rules

| Resource | Inbound | Outbound |
|----------|---------|----------|
| ALB | 443 from internet | 8000, 3000, 8001, 80 to private subnet |
| CMS API Pods | 8000 from ALB only | 5432 to PG, 6379 to Redis, 7700 to Meilisearch, 443 via NAT |
| Worker Pods | None | 5432 to PG, 6379 to Redis, 443 via NAT |
| WebSocket Pods | 8001 from ALB only | 5432 to PG, 6379 to Redis |
| Frontend Pods | 3000 from ALB only | 8000 to API Pods |
| PostgreSQL | 5432 from API/Worker pods only | None |
| Redis | 6379 from API/Worker pods only | None |
| Meilisearch | 7700 from API pods only | None |

---

## DNS Configuration

```mermaid
graph LR
    Domain["example.com (A record → CDN)"]
    API["api.example.com (A record → ALB)"]
    Admin["admin.example.com (A record → ALB)"]
    Media["media.example.com (CNAME → CDN origin)"]
    WS["ws.example.com (A record → ALB, WebSocket upgrade)"]

    Domain --> CDN[CDN]
    API --> ALB[ALB]
    Admin --> ALB
    Media --> CDN
    WS --> ALB
```

---

## TLS / Certificate Strategy

| Domain | Certificate | Renewal |
|--------|-------------|---------|
| `example.com` | ACM / Let's Encrypt wildcard | Auto-renew |
| `api.example.com` | ACM / Let's Encrypt | Auto-renew |
| `admin.example.com` | ACM / Let's Encrypt | Auto-renew |
| `media.example.com` | CDN-managed | Auto-renew |
| All | TLS 1.2 minimum, TLS 1.3 preferred | — |

---

## Network Monitoring

| Tool | Purpose |
|------|---------|
| VPC Flow Logs | Capture all traffic for security audit |
| CloudWatch / Cloud Monitoring | Metrics for ALB, API pods, DB connections |
| WAF Logs | Log blocked requests; alert on anomalies |
| Uptime Checks | Synthetic monitoring every 60 s from multiple regions |
| PagerDuty | Alerting for P1 availability and security incidents |
