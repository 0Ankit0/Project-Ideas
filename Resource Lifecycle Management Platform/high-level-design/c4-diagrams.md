# C4 Diagrams

C4 model views (Context, Container, Component) for the **Resource Lifecycle Management Platform**.

---

## Level 1 – System Context

> Who uses the system and what other systems does it talk to?

```mermaid
flowchart TB
  Requestor(["👤 Requestor"])
  Custodian(["👤 Custodian"])
  Manager(["👤 Resource Manager"])
  Compliance(["👤 Compliance Officer"])
  Finance(["👤 Finance"])
  Ops(["👤 Operations"])

  RLMP["🖥️ Resource Lifecycle\nManagement Platform"]

  IAM["🔐 Identity Provider\n[External System]"]
  Ledger["💰 Financial Ledger\n[External System]"]
  SIEM_box["🔍 SIEM\n[External System]"]
  Notif["📬 Notification Service\n[External System]"]
  ERP["🏢 ERP / CMDB\n[External System]"]

  Requestor -- "HTTPS" --> RLMP
  Custodian -- "HTTPS / Scanner" --> RLMP
  Manager -- "HTTPS" --> RLMP
  Compliance -- "HTTPS" --> RLMP
  Finance -- "HTTPS" --> RLMP
  Ops -- "HTTPS" --> RLMP

  RLMP -- "OAuth2/OIDC" --> IAM
  RLMP -- "Async Events" --> Ledger
  RLMP -- "Event Stream" --> SIEM_box
  RLMP -- "HTTP / Queue" --> Notif
  RLMP -- "REST Sync" --> ERP
```

---

## Level 2 – Container Diagram

> What containers make up the RLMP system?

```mermaid
flowchart TB
  Actor(["👥 All Actors"])

  subgraph RLMP_System["Resource Lifecycle Management Platform"]
    WebApp["🌐 Web Application\n[Container: React SPA]\nManagement UI for\nmanagers, compliance, finance"]
    MobileApp["📱 Mobile App\n[Container: React Native]\nScanner + requestor\ninterface"]
    APIGW["🔀 API Gateway\n[Container: Kong / AWS APIGW]\nAuth, routing, rate limiting"]
    CoreAPI["⚙️ Core API\n[Container: Node.js / Go service]\nCommand handling for all\nlifecycle operations"]
    PolicyEng["📋 Policy Engine\n[Container: OPA sidecar]\nQuota, eligibility,\npriority evaluation"]
    WorkerPool["🔄 Worker Pool\n[Container: Queue consumers]\nAsync event processing,\noverdue detection, archive"]
    SearchAPI["🔍 Search API\n[Container: Elasticsearch]\nCatalog search,\navailability queries"]
    PrimaryDB["🗄️ PostgreSQL\n[Container: Primary DB]\nAll write-path data"]
    ReadReplica["🗄️ PostgreSQL Read Replica\n[Container: Read DB]\nReporting, projections"]
    Redis["⚡ Redis\n[Container: Cache]\nPolicy cache,\nidempotency keys"]
    EventBus["📨 Event Bus\n[Container: Kafka]\nDomain event streaming"]
    ColdStore["📦 Object Storage\n[Container: S3 / GCS]\nArchived resource records"]
  end

  IAM_ext["🔐 Identity Provider"]
  Ledger_ext["💰 Financial Ledger"]
  SIEM_ext["🔍 SIEM"]
  Notif_ext["📬 Notification Service"]

  Actor --> WebApp
  Actor --> MobileApp
  WebApp -- "HTTPS API calls" --> APIGW
  MobileApp -- "HTTPS API calls" --> APIGW
  APIGW -- "JWT validation" --> IAM_ext
  APIGW -- "Route" --> CoreAPI
  CoreAPI -- "Evaluate policy" --> PolicyEng
  CoreAPI -- "Read/Write" --> PrimaryDB
  CoreAPI -- "Cache" --> Redis
  CoreAPI -- "Outbox relay" --> EventBus
  EventBus -- "Consume" --> WorkerPool
  WorkerPool -- "Index" --> SearchAPI
  WorkerPool -- "Projections" --> ReadReplica
  WorkerPool -- "Events" --> Ledger_ext
  WorkerPool -- "Events" --> SIEM_ext
  WorkerPool -- "Send" --> Notif_ext
  WorkerPool -- "Archive" --> ColdStore
  CoreAPI -- "Search queries" --> SearchAPI
  CoreAPI -- "Report queries" --> ReadReplica
```

---

## Level 3 – Component Diagram (Core API Container)

> What components live inside the Core API container?

```mermaid
flowchart LR
  subgraph CoreAPI["Core API Container"]
    Router["HTTP Router\n(Express / Chi)\nRoute → Controller"]
    ProvCtrl["Provisioning Controller\nPOST /resources\nBulk import"]
    AllocCtrl["Allocation Controller\nPOST /reservations\nDELETE /reservations/{id}"]
    CustCtrl["Custody Controller\nPOST /allocations\n/checkin /force-return"]
    IncidentCtrl["Incident Controller\nGET/POST /incidents"]
    SettleCtrl["Settlement Controller\nPOST /settlements\n/dispute /void"]
    DecomCtrl["Decommission Controller\nPOST /resources/{id}/decommission"]
    AuditCtrl["Audit Controller\nGET /audit/resources/{id}"]

    CmdHandler["Command Handler\nValidate → Authorize → Execute"]
    StateMachine["State Machine Engine\nTransition guards\nCompensation logic"]
    PolicyAdapter["Policy Adapter\nOPA client\nDecision cache"]
    OutboxPub["Outbox Publisher\nWrites to outbox table\nSame DB transaction"]
    Repo["Repository Layer\nPostgreSQL queries\nOptimistic locking"]
  end

  Router --> ProvCtrl & AllocCtrl & CustCtrl & IncidentCtrl & SettleCtrl & DecomCtrl & AuditCtrl
  ProvCtrl & AllocCtrl & CustCtrl & IncidentCtrl & SettleCtrl & DecomCtrl --> CmdHandler
  CmdHandler --> PolicyAdapter
  CmdHandler --> StateMachine
  StateMachine --> Repo
  StateMachine --> OutboxPub
  Repo --> PG[("PostgreSQL")]
  OutboxPub --> PG
```

---

## Cross-References

- Detailed component diagrams: [../detailed-design/c4-component-diagram.md](../detailed-design/c4-component-diagram.md)
- Infrastructure deployment: [../infrastructure/deployment-diagram.md](../infrastructure/deployment-diagram.md)
- System context narrative: [../analysis/system-context-diagram.md](../analysis/system-context-diagram.md)
