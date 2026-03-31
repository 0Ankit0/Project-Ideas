# Deployment Diagram

Production deployment topology for the **Resource Lifecycle Management Platform** on Kubernetes.

---

## Kubernetes Deployment Architecture

```mermaid
flowchart TB
  subgraph Internet["Public Internet"]
    Clients["Web / Mobile / Scanner Clients"]
    ExtSystems["External Systems\n(ERP, Financial Ledger, SIEM)"]
  end

  subgraph CDN["CDN / WAF Layer"]
    WAF["WAF + DDoS Protection\n(CloudFront / Cloudflare)"]
  end

  subgraph IngressCluster["Ingress Cluster (Public Subnet)"]
    ALB["Application Load Balancer\n(HTTPS :443 → HTTP :80)"]
    APIGW_Pod["API Gateway Pods\n(Kong)\n• JWT validation\n• Rate limiting\n• TLS termination\n• 3 replicas minimum"]
  end

  subgraph AppCluster["Application Cluster (Private Subnet)"]
    subgraph CoreAPIDeployment["Core API Deployment"]
      CoreAPI1["Core API Pod 1\n(core-api container)\n(opa-sidecar container)\nPort 8080 / 8181"]
      CoreAPI2["Core API Pod 2"]
      CoreAPI3["Core API Pod 3"]
      CoreAPI_HPA["HPA: 3–20 pods\n(CPU > 70% | RPS > 100)"]
    end

    subgraph WorkerDeployment["Worker Deployment"]
      OutboxWorker["Outbox Relay Pod\n1 replica (leader-elected)\ncron: every 1 s"]
      OverdueWorker["Overdue Detector Pod\n1 replica (leader-elected)\ncron: every 5 min"]
      KafkaConsumers["Kafka Consumer Pods\n(Notification, Search,\nAudit, Settlement,\nEscalation, Archive)\n1–5 replicas per consumer group"]
    end

    subgraph CronJobs["CronJobs"]
      ReconciliationJob["Reconciliation Job\n(daily 02:00 UTC)"]
      ArchiveJob["Archive Job\n(triggered by event)"]
    end
  end

  subgraph DataCluster["Data Cluster (Isolated Subnet)"]
    subgraph PostgreSQL_HA["PostgreSQL HA"]
      PG_Primary["PostgreSQL Primary\n(RDS Multi-AZ / CloudSQL)\n96 GB RAM, 32 vCPU"]
      PG_Replica["Read Replica × 2\n(async replication, ~1s lag)"]
      PG_Primary --> PG_Replica
    end
    subgraph Redis_Cluster["Redis Cluster"]
      Redis1["Redis Node 1\n(Primary)"]
      Redis2["Redis Node 2\n(Replica)"]
      Redis3["Redis Node 3\n(Replica)"]
    end
    subgraph Kafka_Cluster["Kafka Cluster"]
      K1["Kafka Broker 1"]
      K2["Kafka Broker 2"]
      K3["Kafka Broker 3"]
      ZK["ZooKeeper / KRaft"]
    end
    Elasticsearch_Cluster["Elasticsearch Cluster\n(3 nodes, 3 shards/index)"]
    S3_Storage["Object Storage\n(S3 / GCS)\nArchive + Photo Evidence"]
  end

  Clients --> WAF --> ALB --> APIGW_Pod
  APIGW_Pod -->|"mTLS"| CoreAPI1 & CoreAPI2 & CoreAPI3
  CoreAPI1 & CoreAPI2 & CoreAPI3 -->|"pool"| PG_Primary
  CoreAPI1 & CoreAPI2 & CoreAPI3 -->|"read"| PG_Replica
  CoreAPI1 & CoreAPI2 & CoreAPI3 --> Redis1
  OutboxWorker --> PG_Primary
  OutboxWorker --> K1 & K2 & K3
  KafkaConsumers --> K1 & K2 & K3
  KafkaConsumers --> Elasticsearch_Cluster
  KafkaConsumers --> S3_Storage
  OverdueWorker --> PG_Primary
  OverdueWorker --> K1
```

---

## Environment Configuration

| Environment | Purpose | Replicas (Core API) | DB | Notes |
|---|---|---|---|---|
| `dev` | Local development | 1 | Docker Postgres | OPA in single-process mode |
| `ci` | Automated testing | 1 | Ephemeral Postgres (Testcontainers) | No real Kafka; test doubles |
| `staging` | Pre-production validation | 3 | RDS Multi-AZ (smaller instance) | Full Kafka cluster; anonymized prod data |
| `production` | Live service | 3–20 (HPA) | RDS Multi-AZ + 2 read replicas | Full HA; all monitoring enabled |
| `dr` | Disaster recovery | 3 (warm standby) | Cross-region replica | RTO ≤ 30 min; RPO ≤ 5 min |

---

## Resource Requirements

| Service | CPU Request | CPU Limit | Memory Request | Memory Limit | Replicas |
|---|---|---|---|---|---|
| Core API | 500m | 2000m | 512Mi | 2Gi | 3–20 (HPA) |
| OPA Sidecar | 100m | 500m | 128Mi | 512Mi | co-located |
| Outbox Relay | 100m | 500m | 128Mi | 256Mi | 1 |
| Overdue Detector | 100m | 500m | 128Mi | 256Mi | 1 |
| Kafka Consumer (each) | 200m | 1000m | 256Mi | 1Gi | 1–5 |

---

## Health Checks

All pods expose:
- `GET /healthz/live` → liveness probe (returns 200 if process alive)
- `GET /healthz/ready` → readiness probe (returns 200 only if DB connection pool and Redis are reachable)

---

## Cross-References

- Cloud architecture: [cloud-architecture.md](./cloud-architecture.md)
- Network infrastructure: [network-infrastructure.md](./network-infrastructure.md)
- Component diagram: [../detailed-design/component-diagrams.md](../detailed-design/component-diagrams.md)
