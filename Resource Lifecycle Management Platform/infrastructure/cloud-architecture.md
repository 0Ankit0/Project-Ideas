# Cloud Architecture

Multi-region cloud architecture for the **Resource Lifecycle Management Platform** covering compute, data, networking, secrets, observability, and disaster recovery.

---

## Environment Layout

```mermaid
flowchart TB
  subgraph AWS_Primary["AWS Primary Region (us-east-1)"]
    subgraph VPC_Prod["Production VPC (10.0.0.0/16)"]
      subgraph Public["Public Subnets (10.0.1.0/24, 10.0.2.0/24)"]
        ALB_Prod["Application Load Balancer\n(HTTPS 443, HTTP→HTTPS redirect)"]
        NATGateway["NAT Gateway\n(outbound-only for private subnets)"]
      end
      subgraph Private_App["Private App Subnets (10.0.10.0/24, 10.0.11.0/24)"]
        EKS_Nodes["EKS Node Group\n(m6i.2xlarge × 6 min, ×20 max)\nCore API · Workers · Crons"]
      end
      subgraph Private_Data["Private Data Subnets (10.0.20.0/24, 10.0.21.0/24)"]
        RDS_Primary["RDS PostgreSQL 15 Multi-AZ\n(db.r6g.4xlarge, 500 GB gp3)\nEncrypted at rest (KMS)"]
        RDS_Replica["RDS Read Replica × 2\n(async, ~1 s lag)"]
        ElastiCache["ElastiCache Redis 7\n(r6g.xlarge, cluster mode)\n3 primary + 3 replica shards"]
        MSK["Amazon MSK Kafka 3.7\n(kafka.m5.large × 3 brokers)\n12 partitions, replication 3"]
        ES_Cluster["OpenSearch / Elasticsearch 8\n(r6g.large.search × 3 nodes)"]
      end
      subgraph Private_Storage["Isolated Storage"]
        S3_Archive["S3 Bucket\n(lifecycle: Glacier after 90d)\nSSE-S3 + Object Lock (WORM)\nretention per compliance profile"]
        S3_Evidence["S3 Bucket\n(photo evidence)\nSSE-S3 + versioning"]
      end
    end
  end

  subgraph AWS_DR["AWS DR Region (us-west-2)"]
    RDS_CrossRegion["RDS Cross-Region Replica\n(warm standby)\nRTO 30 min, RPO 5 min"]
    MSK_MirrorMaker["Kafka MirrorMaker 2\n(topic replication)"]
    S3_Replicated["S3 Replication\n(cross-region replication enabled)"]
  end

  subgraph SharedServices["Shared Services (All Regions)"]
    Route53["Route 53\n(health-check based failover\nprimary.rlmp.example.com)"]
    CloudFront["CloudFront + WAF\n(DDoS protection, geo-blocking)"]
    Cognito["Amazon Cognito / Auth0\n(OAuth2 / OIDC)"]
    Vault["HashiCorp Vault\n(dynamic DB credentials\nKafka API keys\nRotation: 30 days)"]
    SecretsManager["AWS Secrets Manager\n(TLS certs, API keys)"]
    CloudWatch["CloudWatch + Datadog\n(Metrics, Logs, Traces)"]
    Sentry["Sentry\n(Error tracking)"]
  end

  CloudFront --> ALB_Prod
  ALB_Prod --> EKS_Nodes
  EKS_Nodes --> RDS_Primary
  EKS_Nodes --> RDS_Replica
  EKS_Nodes --> ElastiCache
  EKS_Nodes --> MSK
  EKS_Nodes --> ES_Cluster
  EKS_Nodes --> S3_Archive
  EKS_Nodes --> S3_Evidence
  RDS_Primary --> RDS_CrossRegion
  MSK --> MSK_MirrorMaker --> MSK_MirrorMaker
  S3_Archive --> S3_Replicated
  EKS_Nodes --> Vault
  EKS_Nodes --> CloudWatch
  Route53 --> CloudFront
```

---

## DR Failover Procedure

```mermaid
flowchart TD
  Detect[Alert: Primary Region Unreachable] --> Assess{Confirm region failure\n(Route 53 health check fails)}
  Assess -->|False alarm| Resume[Continue on Primary]
  Assess -->|Confirmed| PromoteReplica[Promote RDS Cross-Region Replica\n(~5 min)]
  PromoteReplica --> PointKafka[Redirect Kafka producers\nto DR MSK cluster]
  PointKafka --> UpdateDNS[Update Route 53 failover record\nto DR ALB]
  UpdateDNS --> ScaleEKS[Scale DR EKS node group\nto production capacity]
  ScaleEKS --> SmokeTest[Run smoke test suite\nagainst DR endpoint]
  SmokeTest -->|Pass| TrafficLive[100% traffic on DR\nRTO achieved]
  SmokeTest -->|Fail| Rollback[Investigate and escalate\nto incident commander]
```

---

## Security Architecture

| Control | Implementation | Validation |
|---|---|---|
| Encryption in transit | TLS 1.3 minimum, mTLS between services | Quarterly TLS scan |
| Encryption at rest | KMS-managed keys for RDS, S3, ElastiCache | Key rotation audit annually |
| IAM / RBAC | EKS IRSA; least-privilege IAM roles per service | IAM Access Analyzer weekly |
| Secret management | Vault dynamic secrets; no static passwords | Secret rotation log review monthly |
| Network isolation | VPC + security groups + NACLs; no 0.0.0.0/0 egress from data subnets | IaC policy checks (Checkov/OPA) |
| WAF rules | OWASP CRS ruleset; rate limiting; bot mitigation | Monthly WAF rule review |
| Audit logs | CloudTrail + VPC Flow Logs → SIEM (90-day hot, 7-year cold) | SIEM alert on unauthorized API calls |
| Vulnerability scanning | Trivy on container images in CI; Inspector on EC2/ECS | PR gate: no CRITICAL CVEs |
| Penetration testing | Annual external pentest + quarterly internal red team | Remediation within 30 days for critical |

---

## Backup and Recovery

| Data Store | Backup Frequency | Retention | Recovery Method |
|---|---|---|---|
| PostgreSQL | Automated daily snapshot + continuous WAL (5-min RPO) | 35 days point-in-time | RDS restore or WAL replay |
| Redis | RDB snapshot every 15 min | 7 days | ElastiCache snapshot restore |
| Kafka | MirrorMaker 2 to DR region | Infinite (log compaction) | Replay from offset |
| S3 Archive | Versioning + cross-region replication | Compliance retention period | S3 Object Lock prevents deletion |
| Elasticsearch | Automated snapshot to S3 | 30 days | ES snapshot restore |

---

## Cross-References

- Deployment diagram: [deployment-diagram.md](./deployment-diagram.md)
- Network infrastructure: [network-infrastructure.md](./network-infrastructure.md)
- Implementation security guidelines: [../implementation/implementation-guidelines.md](../implementation/implementation-guidelines.md)
