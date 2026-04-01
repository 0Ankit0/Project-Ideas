# C4 Architecture Diagrams

## Level 1: System Context Diagram

Shows Application Hosting Platform in relation to external systems and users.

```mermaid
graph TB
    Developer["👨‍💻 Developer"]
    TeamLead["👤 Team Lead"]
    OpsEng["⚙️ Operations Engineer"]
    
    AHP["Application Hosting Platform<br/>(AHP)"]
    
    GitHub["🐙 GitHub/GitLab"]
    Cloud["☁️ Cloud Provider<br/>AWS/GCP/Azure"]
    AddOns["📦 Add-on Services<br/>Postgres, Redis,<br/>SendGrid"]
    DNS["🌐 DNS Services"]
    SSL["🔒 Let's Encrypt"]
    Stripe["💳 Stripe Payment"]
    Slack["💬 Slack"]
    
    Developer -->|Deploy, Scale<br/>Manage Config| AHP
    TeamLead -->|Manage Team<br/>Billing| AHP
    OpsEng -->|Monitor<br/>Alert| AHP
    
    AHP -->|Push/Pull Code<br/>Webhooks| GitHub
    AHP -->|Provision Resources<br/>Collect Metrics| Cloud
    AHP -->|Provision Services| AddOns
    AHP -->|Verify Domain<br/>Manage Records| DNS
    AHP -->|Request Certs<br/>Renewal| SSL
    AHP -->|Process Payments| Stripe
    AHP -->|Send Notifications| Slack
    
    style AHP fill:#4A90E2,color:#fff
    style Developer fill:#50C878,color:#fff
    style TeamLead fill:#FFB81C,color:#000
    style OpsEng fill:#FF6B6B,color:#fff
```

## Level 2: Container Diagram

Shows major containers (services, databases, external systems) within AHP.

```mermaid
graph TB
    subgraph AHP["Application Hosting Platform"]
        subgraph "Web Tier"
            WebUI["Web Dashboard<br/>[React + TypeScript]<br/>- Application UI<br/>- Deployment History<br/>- Metrics Dashboard<br/>- Billing Portal"]
        end
        
        subgraph "API Tier"
            APIGw["API Gateway<br/>[Node.js/Go]<br/>- Route Requests<br/>- JWT Validation<br/>- Rate Limiting"]
            
            AuthSvc["Auth Service<br/>[Node.js/Python]<br/>- OAuth Integration<br/>- Token Management<br/>- MFA"]
            
            AppSvc["Application Service<br/>[Node.js/Go]<br/>- App CRUD<br/>- Deployment Orchestration<br/>- Configuration Management"]
            
            BillingSvc["Billing Service<br/>[Node.js/Python]<br/>- Usage Tracking<br/>- Invoice Generation<br/>- Payment Processing"]
        end
        
        subgraph "Build & Deploy"
            BuildQueue["Build Queue<br/>[RabbitMQ/SQS]<br/>- Job Storage<br/>- Delivery Guarantee"]
            
            BuildSvc["Build Service<br/>[Docker/Buildkit]<br/>- Language Detection<br/>- Compilation<br/>- Testing<br/>- Image Build"]
            
            Registry["Container Registry<br/>[ECR/GCR]<br/>- Image Storage<br/>- Vulnerability Scan<br/>- Image Versioning"]
            
            DeploySvc["Deploy Service<br/>[Helm/ArgoCD]<br/>- Kubernetes Deployments<br/>- Health Checks<br/>- Traffic Routing<br/>- Rollbacks"]
        end
        
        subgraph "Data Layer"
            PrimaryDB["Primary Database<br/>[Postgres]<br/>- App State<br/>- Deployments<br/>- User Data<br/>- Billing Records"]
            
            CacheLayer["Cache Layer<br/>[Redis]<br/>- Sessions<br/>- Rate Limits<br/>- Job Queue"]
        end
        
        subgraph "Observability"
            MetricsCollector["Metrics Collector<br/>[Prometheus]<br/>- Scrapes /metrics<br/>- Collects System Metrics<br/>- Custom Metrics"]
            
            LogAgg["Log Aggregator<br/>[Fluent-bit/ELK]<br/>- Ships Container Logs<br/>- Aggregates to Storage<br/>- Indexing"]
            
            TSDB["Time Series Database<br/>[Prometheus/InfluxDB]<br/>- Metric Storage<br/>- Time-range Queries<br/>- Aggregation"]
            
            AlertEngine["Alert Engine<br/>[Prometheus Rules]<br/>- Rule Evaluation<br/>- Threshold Detection<br/>- Notification Routing"]
        end
        
        subgraph "Kubernetes Cluster"
            K8s["Kubernetes Control Plane<br/>- Pod Orchestration<br/>- Resource Management<br/>- Auto-scaling<br/>- Service Mesh Integration"]
            
            AppNodes["Application Nodes<br/>- Running Containers<br/>- Metrics Exposure<br/>- Log Streaming"]
        end
    end
    
    subgraph "External Systems"
        GitHub["GitHub/GitLab<br/>- Code Repos<br/>- Webhooks"]
        Cloud["Cloud Provider<br/>- Compute<br/>- Storage<br/>- Networking"]
        AddOns["Add-on Services<br/>- RDS, Redis Cloud<br/>- SendGrid<br/>- S3"]
        DNS["DNS Services<br/>- CNAME Management<br/>- Verification"]
        SSL["Let's Encrypt<br/>- Certificate Issuance<br/>- Auto-renewal"]
        Stripe["Stripe<br/>- Payment Processing<br/>- Webhooks"]
    end
    
    %% Internal Connections
    WebUI --> APIGw
    APIGw --> AuthSvc
    APIGw --> AppSvc
    APIGw --> BillingSvc
    
    AppSvc --> PrimaryDB
    AppSvc --> CacheLayer
    BillingSvc --> PrimaryDB
    
    BuildQueue --> BuildSvc
    BuildSvc --> Registry
    Registry --> DeploySvc
    DeploySvc --> K8s
    
    AppNodes -->|Expose| MetricsCollector
    AppNodes -->|Stream| LogAgg
    MetricsCollector --> TSDB
    LogAgg --> TSDB
    TSDB --> AlertEngine
    
    K8s --> AppNodes
    
    %% External Connections
    APIGw --> GitHub
    APIGw --> Cloud
    APIGw --> AddOns
    APIGw --> DNS
    APIGw --> SSL
    BillingSvc --> Stripe
    
    style AHP fill:#e1f5ff
    style GitHub fill:#333,color:#fff
    style Cloud fill:#FF9900
    style Stripe fill:#635BFF,color:#fff
```

**Containers:**
- **Web Dashboard**: Single-page application for user interactions
- **API Gateway**: Central routing and authentication layer
- **Auth Service**: JWT and OAuth token management
- **Application Service**: Core business logic for deployments and apps
- **Billing Service**: Usage tracking and invoice generation
- **Build Queue**: Asynchronous job queue (RabbitMQ/SQS)
- **Build Service**: Language-specific compilation and image creation
- **Container Registry**: Image storage and vulnerability scanning
- **Deploy Service**: Kubernetes deployment orchestration
- **Primary Database**: Transactional data storage
- **Cache Layer**: Session and rate limit storage
- **Metrics Collector**: Prometheus-compatible metrics scraper
- **Log Aggregator**: Centralized log shipping
- **Time Series Database**: Metrics and logs storage
- **Alert Engine**: Rule evaluation and notification routing
- **Kubernetes Cluster**: Container orchestration

---

## Level 3: Component Diagram (API & Application Service)

Shows internal components of the Application Service.

```mermaid
graph TB
    subgraph AppService["Application Service"]
        subgraph "Controllers"
            AppCtrl["Application Controller<br/>- GET/POST /applications<br/>- GET/PATCH /applications/{id}"]
            DeployCtrl["Deployment Controller<br/>- POST /applications/{id}/deployments<br/>- GET /deployments/{id}<br/>- POST /deployments/{id}/rollback"]
            ScaleCtrl["Scaling Controller<br/>- PUT /applications/{id}/scaling<br/>- GET /scaling-history"]
            DomainCtrl["Domain Controller<br/>- POST /applications/{id}/domains<br/>- GET /domains/{id}<br/>- PATCH /domains/{id}/verify"]
        end
        
        subgraph "Services"
            DeploymentOrch["Deployment Orchestrator<br/>- Coordinate build → deploy<br/>- Health check logic<br/>- Rollback logic"]
            
            ScalingEngine["Scaling Engine<br/>- Calculate new instance count<br/>- Enforce min/max limits<br/>- Validate quota"]
            
            DomainMgr["Domain Manager<br/>- DNS verification<br/>- SSL coordination<br/>- CNAME management"]
            
            EnvVarMgr["Environment Variable Manager<br/>- Encryption/decryption<br/>- Secret rotation<br/>- Validation"]
        end
        
        subgraph "Data Access"
            AppRepo["Application Repository<br/>- Find by ID<br/>- List by team<br/>- Create/update/delete"]
            
            DeployRepo["Deployment Repository<br/>- Find deployments<br/>- Create deployment record<br/>- Update status"]
            
            DomainRepo["Domain Repository<br/>- Find by name<br/>- Create/update/delete<br/>- Query status"]
        end
        
        subgraph "External Integrations"
            BuildQueueClient["Build Queue Client<br/>- Enqueue build job<br/>- Poll for status"]
            
            K8sClient["Kubernetes Client<br/>- Create deployment<br/>- Update scaling<br/>- Get status"]
            
            DNSClient["DNS Provider Client<br/>- Query DNS<br/>- Verify CNAME"]
            
            AddOnClient["Add-on Provider Client<br/>- Provision service<br/>- Get credentials<br/>- Deprovision"]
        end
    end
    
    subgraph Database
        DB["PostgreSQL<br/>- Applications<br/>- Deployments<br/>- Domains"]
    end
    
    %% Controller to Service
    AppCtrl --> AppRepo
    DeployCtrl --> DeploymentOrch
    DeployCtrl --> DeployRepo
    ScaleCtrl --> ScalingEngine
    DomainCtrl --> DomainMgr
    
    %% Service to Client/Repo
    DeploymentOrch --> BuildQueueClient
    DeploymentOrch --> K8sClient
    ScalingEngine --> K8sClient
    DomainMgr --> DNSClient
    EnvVarMgr --> AppRepo
    
    %% Repository to DB
    AppRepo --> DB
    DeployRepo --> DB
    DomainRepo --> DB
    
    style AppService fill:#e1f5ff
    style DB fill:#fff9e6
```

---

**Document Version**: 1.0
**Last Updated**: 2024
