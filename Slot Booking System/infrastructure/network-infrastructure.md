# Network / Infrastructure Diagram - Slot Booking System

> **Platform Independence**: Shows network topology applicable to any hosting environment.

---

## Overview

The Network Infrastructure Diagram shows how network components are organized and connected.

---

## Network Architecture

```mermaid
graph TB
    subgraph "Internet"
        USERS((Users))
        ATTACKERS((Threat Actors))
    end
    
    subgraph "Edge Network"
        DNS[DNS Service<br/>Geo-routing]
        CDN[CDN<br/>Global PoPs]
        DDOS[DDoS Protection]
    end
    
    subgraph "DMZ - 10.0.0.0/24"
        WAF[Web Application<br/>Firewall]
        LB[Load Balancer<br/>SSL Termination]
    end
    
    subgraph "Application Zone - 10.0.1.0/24"
        subgraph "API Subnet"
            API1[API Server<br/>10.0.1.10]
            API2[API Server<br/>10.0.1.11]
            API3[API Server<br/>10.0.1.12]
        end
        
        subgraph "Worker Subnet"
            W1[Worker<br/>10.0.1.20]
            W2[Worker<br/>10.0.1.21]
        end
    end
    
    subgraph "Data Zone - 10.0.2.0/24"
        DB_PRIMARY[(DB Primary<br/>10.0.2.10)]
        DB_REPLICA[(DB Replica<br/>10.0.2.11)]
        REDIS[(Redis Cluster<br/>10.0.2.20-22)]
        MQ[Message Queue<br/>10.0.2.30]
    end
    
    subgraph "Management Zone - 10.0.3.0/24"
        BASTION[Bastion Host<br/>10.0.3.10]
        MONITOR[Monitoring<br/>10.0.3.20]
        LOG[Log Aggregator<br/>10.0.3.21]
    end
    
    USERS --> DNS
    DNS --> CDN
    CDN --> DDOS
    ATTACKERS -.->|Blocked| DDOS
    DDOS --> WAF
    WAF --> LB
    
    LB -->|HTTPS| API1
    LB -->|HTTPS| API2
    LB -->|HTTPS| API3
    
    API1 -->|5432| DB_PRIMARY
    API1 -->|6379| REDIS
    API1 -->|5672| MQ
    
    MQ --> W1
    MQ --> W2
    
    DB_PRIMARY -->|Replication| DB_REPLICA
    
    BASTION -->|SSH| API1
    BASTION -->|SSH| DB_PRIMARY
    
    API1 -->|Metrics| MONITOR
    API1 -->|Logs| LOG
```

---

## Security Zones

| Zone | CIDR | Access Level | Purpose |
|------|------|--------------|---------|
| **DMZ** | 10.0.0.0/24 | Public | Edge services |
| **Application** | 10.0.1.0/24 | Private | Application servers |
| **Data** | 10.0.2.0/24 | Restricted | Databases, caches |
| **Management** | 10.0.3.0/24 | Admin only | Ops, monitoring |

---

## Firewall Rules

| From | To | Port | Protocol | Action |
|------|-----|------|----------|--------|
| Internet | LB | 443 | HTTPS | Allow |
| LB | API Servers | 3000 | HTTP | Allow |
| API Servers | DB | 5432 | TCP | Allow |
| API Servers | Redis | 6379 | TCP | Allow |
| API Servers | MQ | 5672 | AMQP | Allow |
| Bastion | All Internal | 22 | SSH | Allow |
| All | All | * | * | Deny |

---

## Network Security Controls

```mermaid
graph LR
    subgraph "Defense in Depth"
        A[DDoS Protection] --> B[WAF]
        B --> C[Load Balancer]
        C --> D[Network ACLs]
        D --> E[Security Groups]
        E --> F[Application]
    end
```

| Layer | Control | Purpose |
|-------|---------|---------|
| Edge | DDoS Protection | Absorb volumetric attacks |
| Edge | WAF | Block OWASP Top 10 |
| Network | Network ACLs | Subnet-level filtering |
| Instance | Security Groups | Instance-level firewall |
| Application | Rate Limiting | Prevent abuse |

---

## High Availability Setup

```mermaid
graph TB
    subgraph "Availability Zone 1"
        LB1[LB Instance]
        API1[API Server]
        DB1[(DB Primary)]
    end
    
    subgraph "Availability Zone 2"
        LB2[LB Instance]
        API2[API Server]
        DB2[(DB Standby)]
    end
    
    GLB[Global Load<br/>Balancer] --> LB1
    GLB --> LB2
    
    LB1 --> API1
    LB2 --> API2
    
    API1 --> DB1
    API2 --> DB1
    
    DB1 -.->|Sync Replication| DB2
```

---

## VPN / Bastion Access

```mermaid
sequenceDiagram
    participant Admin
    participant Bastion
    participant API as API Server
    participant DB as Database
    
    Admin->>Bastion: SSH (Public Key)
    Bastion->>Bastion: Verify access
    Bastion->>API: SSH Tunnel
    
    Admin->>Bastion: DB Connect Request
    Bastion->>DB: Proxy Connection
    DB-->>Bastion: Connection OK
    Bastion-->>Admin: DB Session
```
