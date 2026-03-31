# Network Infrastructure

Network topology, security group rules, traffic flow, and service mesh configuration for the **Resource Lifecycle Management Platform**.

---

## Network Topology

```mermaid
flowchart TB
  Internet(["🌐 Internet"]) --> WAF_CF["CloudFront + WAF\nDDoS protection\ngeo-blocking\nOWASP CRS rules"]

  WAF_CF --> ALB["Application Load Balancer\nPublic subnet\nHTTPS :443\nHTTP → HTTPS redirect"]

  subgraph VPC["VPC 10.0.0.0/16"]
    subgraph PublicSubnets["Public Subnets\n10.0.1.0/24  10.0.2.0/24\n(Multi-AZ)"]
      ALB
      NATgw["NAT Gateway\n(one per AZ)\nStatic Elastic IP"]
    end

    subgraph AppSubnets["Private App Subnets\n10.0.10.0/24  10.0.11.0/24"]
      APIGW_Pods["API Gateway Pods (Kong)\nPort 8080"]
      CoreAPI_Pods["Core API Pods\nPort 8080"]
      Worker_Pods["Worker Pods\n(Kafka consumers, crons)"]
    end

    subgraph DataSubnets["Private Data Subnets\n10.0.20.0/24  10.0.21.0/24"]
      Postgres["PostgreSQL RDS\nPort 5432"]
      Redis_Cache["Redis ElastiCache\nPort 6379"]
      Kafka_MSK["Kafka MSK\nPort 9092 (SASL/TLS)"]
      ES["Elasticsearch\nPort 9200"]
    end

    subgraph StorageSubnet["VPC Endpoint / Gateway"]
      S3_EP["S3 VPC Endpoint\n(no NAT needed for S3)"]
    end
  end

  ALB -->|"HTTPS → HTTP"| APIGW_Pods
  APIGW_Pods -->|"mTLS\n10.0.10.0/24 → 10.0.10.0/24"| CoreAPI_Pods
  CoreAPI_Pods -->|"TCP 5432"| Postgres
  CoreAPI_Pods -->|"TCP 6379"| Redis_Cache
  CoreAPI_Pods -->|"TCP 9092 SASL/TLS"| Kafka_MSK
  CoreAPI_Pods -->|"TCP 9200 TLS"| ES
  Worker_Pods -->|"TCP 9092"| Kafka_MSK
  Worker_Pods -->|"TCP 5432"| Postgres
  Worker_Pods -->|"S3 API"| S3_EP
  AppSubnets -->|"outbound only"| NATgw
  NATgw --> Internet
```

---

## Security Group Rules

### SG: api-gateway
| Direction | Port | Protocol | Source / Dest | Purpose |
|---|---|---|---|---|
| Inbound | 8080 | TCP | ALB security group | Receive proxied requests |
| Outbound | 8080 | TCP | core-api security group | Forward to Core API |
| Outbound | 443 | TCP | Identity Provider IP ranges | JWT validation |

### SG: core-api
| Direction | Port | Protocol | Source / Dest | Purpose |
|---|---|---|---|---|
| Inbound | 8080 | TCP | api-gateway security group | Accept requests |
| Outbound | 5432 | TCP | postgres security group | DB queries |
| Outbound | 6379 | TCP | redis security group | Cache operations |
| Outbound | 9092 | TCP | kafka security group | Outbox events |
| Outbound | 9200 | TCP | elasticsearch security group | Search queries |
| Outbound | 8181 | TCP | localhost (OPA sidecar) | Policy evaluation |

### SG: postgres
| Direction | Port | Protocol | Source / Dest | Purpose |
|---|---|---|---|---|
| Inbound | 5432 | TCP | core-api security group | Application queries |
| Inbound | 5432 | TCP | worker security group | Worker jobs |
| Inbound | 5432 | TCP | bastion security group | Admin access |
| Outbound | — | All | None | No direct outbound |

### SG: kafka
| Direction | Port | Protocol | Source / Dest | Purpose |
|---|---|---|---|---|
| Inbound | 9092 | TCP | core-api security group | Producer |
| Inbound | 9092 | TCP | worker security group | Consumer |
| Outbound | — | All | None | Managed service |

---

## Service Mesh (Optional – Istio)

When Istio is enabled (recommended for production):
- mTLS is enforced **automatically** between all pods in the mesh.
- Explicit `PeerAuthentication` policy set to `STRICT` for the `rlmp` namespace.
- `AuthorizationPolicy` restricts core-api → postgres to only the `core-api` service account.
- Traffic to external systems uses Istio `ServiceEntry` objects (no ad-hoc egress allowed).

```mermaid
flowchart LR
  subgraph Mesh["Istio Service Mesh (rlmp namespace)"]
    APIGW_SM["API Gateway\n(sidecar: Envoy)"]
    CoreAPI_SM["Core API\n(sidecar: Envoy)"]
    Workers_SM["Workers\n(sidecar: Envoy)"]
  end
  APIGW_SM <-->|"mTLS"| CoreAPI_SM
  CoreAPI_SM <-->|"mTLS"| Workers_SM
  CoreAPI_SM -->|"ServiceEntry"| Postgres
  CoreAPI_SM -->|"ServiceEntry"| Kafka_MSK
```

---

## DNS and Load Balancing

| FQDN | Target | Routing |
|---|---|---|
| `api.rlmp.example.com` | CloudFront → ALB → API Gateway | Active-active, health-check based |
| `api-dr.rlmp.example.com` | DR ALB → DR API Gateway | Active only during failover |
| Internal: `core-api.rlmp.svc.cluster.local` | Kubernetes ClusterIP | Service DNS within cluster |
| Internal: `postgres-primary.rlmp.svc.cluster.local` | PostgreSQL primary | RDS CNAME via ExternalName service |

---

## Cross-References

- Cloud architecture: [cloud-architecture.md](./cloud-architecture.md)
- Deployment diagram: [deployment-diagram.md](./deployment-diagram.md)
- Security edge cases: [../edge-cases/security-and-compliance.md](../edge-cases/security-and-compliance.md)
