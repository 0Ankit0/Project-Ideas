# Network Infrastructure & Security

This document defines the production network topology, ingress/egress policy, edge security, TLS lifecycle, secret-management boundaries, and observability data paths.

## Traceability
- Requirements baseline: [`../requirements/requirements.md`](../requirements/requirements.md)
- Architecture context: [`../high-level-design/architecture-diagram.md`](../high-level-design/architecture-diagram.md)
- Component contracts: [`../detailed-design/component-diagrams.md`](../detailed-design/component-diagrams.md)
- Execution policy: [`../implementation/implementation-guidelines.md`](../implementation/implementation-guidelines.md)

## 1) VPC and Subnet Layout

```mermaid
flowchart TB
  Internet((Internet)) --> EdgeDNS[Authoritative DNS]
  EdgeDNS --> CDN[Global CDN + WAF]
  CDN --> ALB[Regional Public ALB]

  subgraph VPC_Primary[Primary Region VPC 10.20.0.0/16]
    subgraph AZ1[AZ-a]
      PubA[Public Subnet 10.20.0.0/24\nNAT + ALB nodes]
      PrivA[Private App Subnet 10.20.10.0/24\nK8s worker nodes]
      DataA[Private Data Subnet 10.20.20.0/24\nDB primary/replica]
    end
    subgraph AZ2[AZ-b]
      PubB[Public Subnet 10.20.1.0/24]
      PrivB[Private App Subnet 10.20.11.0/24]
      DataB[Private Data Subnet 10.20.21.0/24]
    end
    subgraph AZ3[AZ-c]
      PubC[Public Subnet 10.20.2.0/24]
      PrivC[Private App Subnet 10.20.12.0/24]
      DataC[Private Data Subnet 10.20.22.0/24]
    end

    ALB --> Ingress[Ingress Gateway]
    Ingress --> PrivA
    Ingress --> PrivB
    Ingress --> PrivC
    PrivA --> DataA
    PrivB --> DataB
    PrivC --> DataC
    PrivA --> Obs[Observability Cluster]
  end
```

### Invariants
- No workload pod gets a public IP.
- Data subnets accept only app-tier security-group traffic on approved ports.
- Ingress is centralized through CDN/WAF and regional ALB; direct node ingress is denied.

### Operational acceptance criteria
- NACL/security-group regression tests pass before change approval.
- Quarterly network reachability tests prove denied east-west paths remain denied.
- Drift detection reconciles all subnet route tables within 15 minutes.

## 2) Ingress and Egress Policy

```mermaid
flowchart LR
  Client --> CDNWAF[CDN + WAF]
  CDNWAF --> ALB[ALB :443]
  ALB --> IGW[Ingress Gateway]
  IGW --> SVC[App Services]
  SVC --> EPR[Approved Egress Proxy]
  EPR --> Ext[(External APIs)]

  SVC -. blocked .-> Deny[Unapproved internet destinations]
```

### Policy controls
- **Ingress allowlist**: 443/TCP only, with WAF managed rules + custom tenant signatures.
- **mTLS internal traffic**: service mesh enforces mTLS for service-to-service calls.
- **Egress control**: default deny; explicit allow via egress proxy + DNS policy.
- **Admin access**: SSO + short-lived privileged sessions through bastionless access proxy.

### Invariants
- Default-deny egress and east-west traffic for all namespaces.
- Every cross-service request carries tenant and trace identity headers.

### Operational acceptance criteria
- Daily WAF signature update job completes with zero stale rule packs.
- Monthly egress audit shows 100% destination coverage by approved policy IDs.

## 3) WAF/CDN Path, DNS, and TLS Lifecycle

```mermaid
sequenceDiagram
  participant U as User Browser
  participant D as DNS Provider
  participant C as CDN+WAF
  participant A as ALB
  participant T as TLS Manager

  U->>D: Resolve app.customer.com
  D-->>U: CNAME to edge.ahp.example
  U->>C: TLS handshake (SNI app.customer.com)
  C->>T: Fetch cert from secret store
  C->>A: Forward validated HTTPS request
  A-->>C: Upstream response
  C-->>U: Cached or pass-through response
```

### TLS lifecycle
1. Domain verification via TXT/CNAME challenge.
2. ACME issuance and keypair generation in managed KMS/HSM.
3. Certificate + private key stored in secret manager (versioned).
4. Auto-renew at T-30 days; deploy at edge via zero-downtime rotation.
5. Expiry SLO: no certificate under 14-day lifetime without active renewal ticket.

### Invariants
- Private keys are non-exportable from managed key boundary.
- DNS, certificate, and edge configuration changes are fully audited.

### Operational acceptance criteria
- Synthetic HTTPS checks pass from at least 6 global probes every minute.
- Renewal failure raises page within 5 minutes and opens an incident automatically.

## 4) Secret Management and Observability Stack

```mermaid
flowchart TB
  subgraph SecretPlane
    Vault[Secret Manager + KMS]
    Rotator[Automated Rotation Jobs]
    Workloads[K8s Workloads]
  end

  subgraph Observability
    OTel[OpenTelemetry Collectors]
    Prom[Prometheus]
    Loki[Loki/Log Store]
    Tempo[Trace Store]
    Alert[Alertmanager]
    SRE[SRE On-call]
  end

  Vault -->|short-lived tokens| Workloads
  Rotator --> Vault
  Workloads --> OTel
  OTel --> Prom
  OTel --> Loki
  OTel --> Tempo
  Prom --> Alert
  Loki --> Alert
  Tempo --> Alert
  Alert --> SRE
```

### Invariants
- Secrets are consumed via workload identity; static long-lived credentials are prohibited.
- Metrics/log/trace streams include tenant_id and deployment_id labels.

### Operational acceptance criteria
- 100% of production secrets rotate at or before policy TTL.
- Golden signals (latency, traffic, errors, saturation) available within 60 seconds.

---

**Status**: Complete  
**Document Version**: 2.0
