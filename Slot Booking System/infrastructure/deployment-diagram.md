# Deployment Diagram - Slot Booking System

> **Platform Independence**: Shows software-to-hardware mapping independent of specific vendors.

---

## Overview

The Deployment Diagram shows how software components are deployed onto hardware nodes.

---

## Production Deployment

```mermaid
graph TB
    subgraph "Internet"
        USERS((Users))
    end
    
    subgraph "Edge Layer"
        CDN[CDN Node<br/>Static Assets]
        WAF[WAF<br/>Security]
    end
    
    subgraph "Load Balancer Layer"
        LB[Load Balancer<br/>SSL Termination]
    end
    
    subgraph "Application Tier"
        subgraph "API Cluster"
            API1[API Server 1<br/>Container: Node.js]
            API2[API Server 2<br/>Container: Node.js]
            API3[API Server N<br/>Container: Node.js]
        end
        
        subgraph "Worker Cluster"
            W1[Worker 1<br/>Background Jobs]
            W2[Worker 2<br/>Background Jobs]
        end
        
        subgraph "Scheduler"
            SCHED[Scheduler<br/>Cron Jobs]
        end
    end
    
    subgraph "Data Tier"
        subgraph "Database Cluster"
            DB_PRIMARY[(Primary DB<br/>PostgreSQL)]
            DB_REPLICA[(Read Replica<br/>PostgreSQL)]
        end
        
        subgraph "Cache Cluster"
            REDIS1[(Redis Primary)]
            REDIS2[(Redis Replica)]
        end
        
        MQ[Message Queue<br/>RabbitMQ Cluster]
        
        ES[(Elasticsearch<br/>Cluster)]
    end
    
    subgraph "Storage"
        S3[Object Storage<br/>Images, Files]
    end
    
    USERS --> CDN
    CDN --> WAF
    WAF --> LB
    
    LB --> API1
    LB --> API2
    LB --> API3
    
    API1 --> DB_PRIMARY
    API2 --> DB_PRIMARY
    API3 --> DB_PRIMARY
    
    API1 --> REDIS1
    API1 --> ES
    API1 --> S3
    
    API1 --> MQ
    MQ --> W1
    MQ --> W2
    
    SCHED --> MQ
    
    DB_PRIMARY --> DB_REPLICA
    REDIS1 --> REDIS2
```

---

## Container Deployment (Kubernetes)

```mermaid
graph TB
    subgraph "Kubernetes Cluster"
        subgraph "Ingress"
            ING[Ingress Controller<br/>nginx-ingress]
        end
        
        subgraph "Namespace: slot-booking"
            subgraph "API Deployment"
                API_DEPLOY[Deployment: api<br/>replicas: 3]
                API_SVC[Service: api-svc<br/>ClusterIP]
                API_HPA[HPA<br/>min:3, max:10]
            end
            
            subgraph "Worker Deployment"
                WORKER_DEPLOY[Deployment: worker<br/>replicas: 2]
            end
            
            subgraph "Scheduler"
                CRON_JOB[CronJob: scheduler]
            end
            
            subgraph "ConfigMaps & Secrets"
                CM[ConfigMap:<br/>app-config]
                SEC[Secret:<br/>app-secrets]
            end
        end
        
        subgraph "Namespace: data"
            subgraph "StatefulSets"
                PG_SS[StatefulSet: postgres<br/>replicas: 2]
                REDIS_SS[StatefulSet: redis<br/>replicas: 2]
            end
            
            subgraph "Services"
                PG_SVC[Service: postgres-svc]
                REDIS_SVC[Service: redis-svc]
            end
            
            subgraph "PersistentVolumeClaims"
                PG_PVC[PVC: postgres-data]
                REDIS_PVC[PVC: redis-data]
            end
        end
    end
    
    ING --> API_SVC
    API_SVC --> API_DEPLOY
    API_HPA --> API_DEPLOY
    
    API_DEPLOY --> CM
    API_DEPLOY --> SEC
    API_DEPLOY --> PG_SVC
    API_DEPLOY --> REDIS_SVC
    
    WORKER_DEPLOY --> CM
    WORKER_DEPLOY --> SEC
    WORKER_DEPLOY --> PG_SVC
    WORKER_DEPLOY --> REDIS_SVC
```

---

## Node Specifications

| Node | Specs | Purpose |
|------|-------|---------|
| **API Server** | 2 vCPU, 4GB RAM | Handle HTTP requests |
| **Worker** | 2 vCPU, 4GB RAM | Process async jobs |
| **Database** | 4 vCPU, 16GB RAM, SSD | Data persistence |
| **Redis** | 2 vCPU, 8GB RAM | Caching, locks |
| **Elasticsearch** | 4 vCPU, 8GB RAM | Search indexing |

---

## Deployment Artifacts

| Artifact | Type | Deployment Target |
|----------|------|-------------------|
| `api-image:v1` | Docker Image | API Servers |
| `worker-image:v1` | Docker Image | Worker Servers |
| `web-app/dist` | Static Files | CDN |
| `mobile-app.apk/.ipa` | Mobile App | App Stores |

---

## Environment Configuration

| Environment | API Replicas | DB Type | Purpose |
|-------------|--------------|---------|---------|
| **Development** | 1 | Local SQLite | Local dev |
| **Staging** | 2 | Managed PostgreSQL | Testing |
| **Production** | 3+ | Managed PostgreSQL (HA) | Live traffic |

---

## Scaling Strategy

```mermaid
graph LR
    subgraph "Horizontal Scaling"
        A[Low Load<br/>2 API pods] --> B[Medium Load<br/>5 API pods]
        B --> C[High Load<br/>10 API pods]
    end
    
    subgraph "Vertical Scaling"
        D[DB: 4 vCPU] --> E[DB: 8 vCPU]
        E --> F[DB: 16 vCPU]
    end
    
    subgraph "Read Scaling"
        G[1 Primary] --> H[1 Primary + 2 Replicas]
    end
```
