# Fleet Management System — Network Infrastructure

## Overview

The network architecture is designed for zero-trust, defense-in-depth security across three AWS Availability Zones. All application traffic flows through clearly defined security tiers: public-facing load balancers in public subnets, compute workloads in private subnets, and databases in isolated database subnets with no outbound internet access. GPS/ELD devices from telematics hardware vendors reach the platform over cellular/satellite via a dedicated VPN connection or the public HTTPS endpoint protected by WAF.

---

## Network Topology Diagram

```mermaid
graph TB
    subgraph "Internet"
        Internet["Internet"]
        GPSDevices["GPS/ELD Devices\n(Cellular/Satellite)"]
        Users["Fleet Managers\nDrivers\nDispatchers"]
    end

    subgraph "AWS VPC: 10.0.0.0/16"
        subgraph "Public Subnets (10.0.1.0/24, 10.0.2.0/24, 10.0.3.0/24)"
            ALB["Application Load Balancer\nPort 443 (HTTPS)\nPort 80 to 443 redirect"]
            NatGW["NAT Gateway\n(one per AZ)"]
            BastionHost["Bastion Host\n(SSH access)"]
        end
        subgraph "Private Subnets (10.0.11.0/24, 10.0.12.0/24, 10.0.13.0/24)"
            EKSNodes["EKS Worker Nodes\nm5.xlarge, m5.2xlarge"]
            KafkaBrokers["MSK Kafka Brokers"]
        end
        subgraph "Database Subnets (10.0.21.0/24, 10.0.22.0/24, 10.0.23.0/24)"
            PostgresRDS["PostgreSQL RDS\n(Multi-AZ)"]
            TimescaleDB["TimescaleDB RDS"]
            RedisCluster["Redis ElastiCache\nCluster Mode"]
        end
        subgraph "VPN / Private Connectivity"
            VPNGateway["AWS VPN Gateway\n(ELD Manufacturer VPN)"]
            PrivateLink["AWS PrivateLink\nS3, SQS, Secrets Manager"]
        end
    end

    subgraph "AWS Cloud - us-west-2 (DR)"
        DrSubnet["DR VPC\n172.16.0.0/16\nVPC Peering"]
    end

    Internet --> ALB
    GPSDevices --> ALB
    GPSDevices --> VPNGateway
    Users --> ALB
    ALB --> EKSNodes
    EKSNodes --> NatGW
    NatGW --> Internet
    EKSNodes --> KafkaBrokers
    EKSNodes --> PostgresRDS
    EKSNodes --> TimescaleDB
    EKSNodes --> RedisCluster
    EKSNodes --> PrivateLink
    VPNGateway --> EKSNodes
    BastionHost --> EKSNodes
    PostgresRDS --> DrSubnet
```

---

## VPC Design

### CIDR and Subnet Allocation

| Subnet Type | AZ-a | AZ-b | AZ-c | Purpose |
|---|---|---|---|---|
| Public | `10.0.1.0/24` | `10.0.2.0/24` | `10.0.3.0/24` | ALB, NAT Gateway, Bastion |
| Private | `10.0.11.0/24` | `10.0.12.0/24` | `10.0.13.0/24` | EKS nodes, MSK brokers |
| Database | `10.0.21.0/24` | `10.0.22.0/24` | `10.0.23.0/24` | RDS, ElastiCache |
| VPN/Transit | `10.0.31.0/24` | — | — | VPN Gateway, PrivateLink endpoints |

DNS hostnames and DNS resolution are enabled on the VPC. Default DHCP option sets use AmazonProvidedDNS (Route 53 Resolver at `10.0.0.2`).

### Route Tables

**Public subnet route table:**
- `0.0.0.0/0` → Internet Gateway
- `10.0.0.0/16` → local

**Private subnet route table (per AZ):**
- `0.0.0.0/0` → NAT Gateway (same AZ)
- `10.0.0.0/16` → local
- `172.16.0.0/16` → VPC Peering Connection (DR)

**Database subnet route table:**
- `10.0.0.0/16` → local only (no internet route)

---

## Security Groups

### `sg-alb` — Application Load Balancer
| Direction | Protocol | Port | Source/Dest | Purpose |
|---|---|---|---|---|
| Inbound | TCP | 443 | `0.0.0.0/0` | HTTPS from internet |
| Inbound | TCP | 80 | `0.0.0.0/0` | HTTP redirect to HTTPS |
| Outbound | TCP | 8000–9000 | `sg-eks-nodes` | Forward to Kong/WS Gateway |

### `sg-eks-nodes` — EKS Worker Nodes
| Direction | Protocol | Port | Source/Dest | Purpose |
|---|---|---|---|---|
| Inbound | TCP | 8000–9000 | `sg-alb` | Traffic from ALB |
| Inbound | TCP | All | `sg-eks-nodes` | Pod-to-pod (same SG) |
| Inbound | TCP | 443 | `sg-vpn` | Traffic from VPN gateway |
| Inbound | TCP | 22 | `sg-bastion` | SSH from bastion only |
| Outbound | All | All | `0.0.0.0/0` | Outbound via NAT (package downloads, external APIs) |

### `sg-msk` — MSK Kafka Brokers
| Direction | Protocol | Port | Source/Dest | Purpose |
|---|---|---|---|---|
| Inbound | TCP | 9094 | `sg-eks-nodes` | SASL/TLS Kafka client connections |
| Inbound | TCP | 9092 | `sg-eks-nodes` | Plaintext (internal only, non-prod) |
| Inbound | TCP | 2181 | `sg-eks-nodes` | ZooKeeper (internal MSK) |
| Outbound | All | All | `sg-msk` | Inter-broker replication |

### `sg-rds` — PostgreSQL RDS and TimescaleDB
| Direction | Protocol | Port | Source/Dest | Purpose |
|---|---|---|---|---|
| Inbound | TCP | 5432 | `sg-eks-nodes` | Application DB connections |
| Inbound | TCP | 5432 | `sg-bastion` | DBA access via bastion |
| Outbound | None | — | — | No outbound rules |

### `sg-redis` — ElastiCache Redis Cluster
| Direction | Protocol | Port | Source/Dest | Purpose |
|---|---|---|---|---|
| Inbound | TCP | 6379 | `sg-eks-nodes` | Redis cluster access |
| Outbound | None | — | — | No outbound rules |

### `sg-bastion` — Bastion Host
| Direction | Protocol | Port | Source/Dest | Purpose |
|---|---|---|---|---|
| Inbound | TCP | 22 | Corporate IP list (CIDR) | SSH from approved office IPs |
| Outbound | TCP | 22 | `sg-eks-nodes`, `sg-rds` | Bastion hop connections |

---

## Network Access Control Lists (NACLs)

### Database Subnet NACL (`nacl-database`)

**Inbound rules:**

| Rule # | Protocol | Port | Source | Action |
|---|---|---|---|---|
| 100 | TCP | 5432 | `10.0.11.0/22` (private subnets) | ALLOW |
| 110 | TCP | 6379 | `10.0.11.0/22` (private subnets) | ALLOW |
| 120 | TCP | 1024–65535 | `10.0.11.0/22` | ALLOW (return traffic) |
| 32766 | All | All | `0.0.0.0/0` | DENY |

**Outbound rules:**

| Rule # | Protocol | Port | Dest | Action |
|---|---|---|---|---|
| 100 | TCP | 1024–65535 | `10.0.11.0/22` | ALLOW (return traffic) |
| 32766 | All | All | `0.0.0.0/0` | DENY |

---

## NAT Gateway

One NAT Gateway is deployed per Availability Zone to prevent single-AZ failures from isolating private subnet egress:

- `nat-gw-1a` in public subnet `10.0.1.0/24` with Elastic IP
- `nat-gw-1b` in public subnet `10.0.2.0/24` with Elastic IP
- `nat-gw-1c` in public subnet `10.0.3.0/24` with Elastic IP

Each private subnet route table points to the NAT Gateway in the same AZ. This design avoids cross-AZ data transfer charges and ensures that a single AZ failure does not impact outbound traffic from the other two AZs.

---

## VPN Connection for ELD Devices

Fleet telematics hardware vendors (e.g., Samsara OEM integrations, Geotab) connect over a site-to-site IPsec VPN:

- **AWS VPN Gateway** attached to the main VPC
- **Customer Gateway:** One per ELD manufacturer, configured with BGP ASN
- **Tunnel configuration:** IKEv2, AES-256, SHA-256 integrity, DH group 14
- **Routing:** Static routes for `172.20.0.0/16` (ELD device network) propagated into private subnet route tables
- **Failover:** Each VPN connection has two tunnels for redundancy; BGP detects failover within 30 seconds
- **Security group:** `sg-vpn` allows inbound TCP 8443 from VPN CIDR to tracking service pods

---

## AWS PrivateLink — VPC Endpoints

All AWS service calls from EKS pods are routed through VPC interface endpoints, eliminating internet traversal:

| Service | Endpoint Type | DNS |
|---|---|---|
| Amazon S3 | Gateway endpoint | Bucket-level routing via route table |
| Amazon SQS | Interface endpoint | `sqs.us-east-1.vpce.amazonaws.com` |
| AWS Secrets Manager | Interface endpoint | `secretsmanager.us-east-1.vpce.amazonaws.com` |
| Amazon ECR (API) | Interface endpoint | `api.ecr.us-east-1.vpce.amazonaws.com` |
| Amazon ECR (DKR) | Interface endpoint | `dkr.ecr.us-east-1.vpce.amazonaws.com` |
| CloudWatch Logs | Interface endpoint | `logs.us-east-1.vpce.amazonaws.com` |
| AWS KMS | Interface endpoint | `kms.us-east-1.vpce.amazonaws.com` |

All interface endpoints are deployed in private subnets across all three AZs with a security group allowing HTTPS (443) from `sg-eks-nodes` only.

---

## DNS Configuration (Route 53)

### Public Hosted Zone: `fleetpro.io`
| Record | Type | Value |
|---|---|---|
| `app.fleetpro.io` | A (Alias) | CloudFront distribution |
| `api.fleetpro.io` | A (Alias) | CloudFront → ALB |
| `ws.fleetpro.io` | A (Alias) | ALB (WebSocket listener) |
| `status.fleetpro.io` | CNAME | StatusPage.io endpoint |

### Private Hosted Zone: `fleet.internal` (associated with VPC)
| Record | Type | Value |
|---|---|---|
| `postgres.fleet.internal` | CNAME | RDS cluster endpoint |
| `postgres-read.fleet.internal` | CNAME | RDS reader endpoint |
| `timescale.fleet.internal` | CNAME | TimescaleDB cluster endpoint |
| `redis.fleet.internal` | CNAME | Redis configuration endpoint |
| `kafka.fleet.internal` | CNAME | MSK bootstrap broker string |

Route 53 Resolver inbound endpoint in private subnets allows on-premises resolution of `fleet.internal` names.

### Health Checks
- HTTP health check on `api.fleetpro.io/health` every 10 seconds from 3 regions
- Failover routing policy: primary `us-east-1` ALB, secondary `us-west-2` DR ALB

---

## SSL/TLS Certificate Management (ACM)

- Wildcard certificate `*.fleetpro.io` issued by ACM in `us-east-1`
- Replicated to `us-east-1` (for ALB) and `us-east-1` (for CloudFront — must be in `us-east-1`)
- Separate wildcard `*.fleet.internal` for internal mTLS between services (managed via cert-manager + ACM PCA)
- **Renewal:** ACM auto-renews public certs 60 days before expiry; alerts fire via CloudWatch Events if renewal fails
- **mTLS:** Kong API Gateway enforces mTLS for all service-to-service traffic using certificates from the private CA

---

## DDoS Protection

**AWS Shield Standard** (included at no cost):
- Active on all ALB, CloudFront, and Route 53 endpoints
- Protects against volumetric (Layer 3/4) and protocol-level attacks
- SYN flood protection, UDP reflection attack mitigation

**AWS WAF** (attached to CloudFront and ALB):
- AWS Managed Rules — Core Rule Set (CWE, OWASP Top 10)
- AWS Managed Rules — SQL database rule group
- AWS Managed Rules — Known Bad Inputs rule group
- Custom rate-based rule: max 2,000 requests per 5 minutes per IP on `/api/v1/gps-pings`
- Custom rate-based rule: max 100 authentication attempts per 5 minutes per IP on `/api/v1/auth`
- Geo-restriction: Block traffic from embargoed countries (OFAC list)
- WAF logs delivered to S3 (`s3://fleet-waf-logs-prod`) with Athena for analysis

---

## VPC Flow Logs

- **Coverage:** All traffic (ACCEPT and REJECT) for the entire VPC
- **Destination:** CloudWatch Logs group `/aws/vpc/fleet-prod-flow-logs`, retention 30 days
- **Also shipped to S3** (`s3://fleet-vpc-flow-logs-prod`) for long-term retention (90 days) and Athena queries
- **Format:** Custom format including `pkt-srcaddr`, `pkt-dstaddr`, `pkt-src-aws-service`, `flow-direction`, `traffic-path`
- **Alerting:** CloudWatch Metric Filter on rejected traffic spikes → SNS → PagerDuty
