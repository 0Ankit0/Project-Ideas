# Network / Infrastructure Diagram - Document Intelligence System

```mermaid
graph TB
    subgraph "Public Subnet - 10.0.1.0/24"
        LB[Load Balancer]
        NAT[NAT Gateway]
    end
    
    subgraph "Private Subnet - App - 10.0.2.0/24"
        API1[API 10.0.2.10]
        API2[API 10.0.2.11]
    end
    
    subgraph "Private Subnet - Workers - 10.0.3.0/24"
        WORKER1[Worker1 10.0.3.10]
        WORKER2[Worker2 10.0.3.11]
    end
    
    subgraph "Private Subnet - AI - 10.0.4.0/24"
        OCR[OCR Service 10.0.4.10]
        NER[NER Service 10.0.4.20]
    end
    
    subgraph "Private Subnet - Data - 10.0.5.0/24"
        DB[(PostgreSQL 10.0.5.10)]
        QUEUE[RabbitMQ 10.0.5.20]
    end
    
    INTERNET((Internet)) --> LB
    LB --> API1
    LB --> API2
    
    API1 --> QUEUE
    API1 --> DB
    
    QUEUE --> WORKER1
    QUEUE --> WORKER2
    
    WORKER1 --> OCR
    WORKER1 --> NER
    WORKER1 --> DB
```

## Firewall Rules

| From | To | Port | Protocol | Purpose |
|------|-----|------|----------|---------|
| Internet | LB | 443 | HTTPS | API access |
| LB | API Servers | 8000 | HTTP | Internal routing |
| API | Workers | - | Internal | Job dispatch |
| Workers | AI Services | 5000 | HTTP | AI inference |
| Workers | Database | 5432 | TCP | Data storage |
| All | NAT | 443 | HTTPS | Outbound (cloud APIs) |

**Security Zones**:
- **DMZ**: Load balancer, NAT gateway
- **Application**: API servers
- **Processing**: Worker nodes
- **AI**: GPU-enabled AI services
- **Data**:Databases, queues
