# Platform Architecture Diagram

## System Architecture Overview

```mermaid
graph TB
    subgraph "Edge Layer"
        CDN["🌍 CDN<br/>CloudFront"]
        LB["⚙️ Load Balancer<br/>Traffic Distribution"]
    end
    
    subgraph "API & Control Plane"
        APIGw["🚪 API Gateway<br/>Authentication<br/>Rate Limiting<br/>Routing"]
        AuthSvc["🔐 Auth Service<br/>JWT Verification<br/>OAuth Integration"]
        AppSvc["📱 Application Service<br/>CRUD Operations<br/>Configuration"]
    end
    
    subgraph "Build & Deployment"
        BuildQueue["📋 Job Queue<br/>RabbitMQ/SQS"]
        BuildSvc["🏗️ Build Service<br/>Buildpack Detection<br/>Compilation<br/>Testing"]
        Registry["🗂️ Container Registry<br/>Image Storage<br/>Vulnerability Scan"]
        DeploySvc["🚀 Deploy Service<br/>Orchestration<br/>Health Checks<br/>Traffic Routing"]
    end
    
    subgraph "Container Orchestration"
        K8s["☸️ Kubernetes Cluster<br/>Pod Scheduling<br/>Resource Management<br/>Auto-scaling<br/>Self-healing"]
        AppNodes["🖥️ Application Nodes<br/>Running Containers"]
    end
    
    subgraph "Data & State"
        PrimaryDB["💾 Postgres<br/>Application State<br/>User Data<br/>Deployments"]
        CacheDB["⚡ Redis<br/>Session Cache<br/>Rate Limit Counters<br/>Job Queue"]
    end
    
    subgraph "Observability"
        MetricsCollector["📊 Metrics Collector<br/>Prometheus Scraper<br/>Custom Metrics"]
        LogAgg["📝 Log Aggregator<br/>Fluent-bit<br/>Elasticsearch"]
        TSDB["⏰ Time Series DB<br/>Prometheus/InfluxDB<br/>Metric Storage"]
        AlertEngine["🔔 Alert Engine<br/>Rule Evaluation<br/>Threshold Detection"]
    end
    
    subgraph "External Integrations"
        GitProvider["🐙 GitHub/GitLab<br/>Repository Integration<br/>Webhooks"]
        CloudProvider["☁️ Cloud Provider<br/>AWS/GCP/Azure<br/>Compute, Storage"]
        DNSProvider["🌐 DNS Provider<br/>Domain Management<br/>Verification"]
        SSLAuth["🔒 SSL Authority<br/>Let's Encrypt<br/>Certificate Issuance"]
        AddOnProviders["📦 Add-on Providers<br/>RDS, Redis Cloud<br/>SendGrid, etc."]
        PaymentProc["💳 Payment Processor<br/>Stripe<br/>Billing"]
        NotifService["📧 Notification Service<br/>Email, Slack<br/>Webhooks"]
    end
    
    subgraph "User Interfaces"
        WebUI["🖥️ Web Dashboard<br/>Applications<br/>Deployments<br/>Metrics<br/>Billing"]
        CLI["⌨️ CLI Tool<br/>Local Development<br/>Script Automation"]
    end
    
    %% Data Plane Connections
    CDN --> LB
    LB --> AppNodes
    AppNodes --> K8s
    
    %% API Layer Connections
    WebUI --> APIGw
    CLI --> APIGw
    APIGw --> AuthSvc
    APIGw --> AppSvc
    AppSvc --> PrimaryDB
    AppSvc --> CacheDB
    
    %% Build & Deploy Connections
    GitProvider -->|Webhook| BuildQueue
    BuildQueue --> BuildSvc
    BuildSvc --> Registry
    Registry --> DeploySvc
    DeploySvc --> K8s
    
    %% Integration Connections
    AppSvc --> GitProvider
    AppSvc --> CloudProvider
    AppSvc --> AddOnProviders
    AppSvc --> DNSProvider
    AppSvc --> SSLAuth
    AppSvc --> PaymentProc
    AppSvc --> NotifService
    
    %% Observability Connections
    AppNodes -->|Expose /metrics| MetricsCollector
    AppNodes -->|Stream logs| LogAgg
    MetricsCollector --> TSDB
    LogAgg --> TSDB
    TSDB --> AlertEngine
    AlertEngine --> NotifService
    
    %% Dashboard Connections
    WebUI -->|Query metrics/logs| TSDB
    WebUI -->|Query state| PrimaryDB
    
    %% Styling
    style CDN fill:#FF9900
    style LB fill:#FF9900
    style APIGw fill:#4A90E2
    style AuthSvc fill:#4A90E2
    style AppSvc fill:#4A90E2
    style K8s fill:#9B59B6
    style AppNodes fill:#9B59B6
    style BuildSvc fill:#FFD700
    style DeploySvc fill:#FFD700
    style TSDB fill:#FF6B6B
    style AlertEngine fill:#FF6B6B
    style WebUI fill:#50C878
    style CLI fill:#50C878
```

## Key System Components

### Edge Layer
- **CDN**: Caches static assets globally (images, CSS, JS)
- **Load Balancer**: Distributes incoming requests across API gateway and application instances

### API & Control Plane
- **API Gateway**: Single entry point for all API calls, authentication, rate limiting, routing
- **Auth Service**: JWT verification, OAuth token handling, multi-factor authentication
- **Application Service**: Business logic for applications, deployments, scaling, configuration

### Build & Deployment
- **Job Queue**: Asynchronous build/deployment requests (RabbitMQ or AWS SQS)
- **Build Service**: Detects language, selects buildpack, compiles code, runs tests, creates container image
- **Container Registry**: Stores container images, scans for vulnerabilities, manages image lifecycle
- **Deploy Service**: Orchestrates Kubernetes deployments, health checks, traffic routing, rollbacks

### Container Orchestration
- **Kubernetes Cluster**: Orchestrates container scheduling, resource management, auto-scaling
- **Application Nodes**: Worker nodes running containerized applications

### Data & State
- **Primary Database (Postgres)**: Application state, deployments, configurations, user data
- **Cache Layer (Redis)**: Session cache, rate limit counters, job queue backing

### Observability
- **Metrics Collector**: Scrapes /metrics endpoint from running containers (Prometheus-compatible)
- **Log Aggregator**: Ships logs from containers to centralized storage (Fluent-bit)
- **Time Series Database**: Stores metrics and logs with timestamps for querying and alerting
- **Alert Engine**: Evaluates alert rules continuously, fires alerts when conditions are met

### External Integrations
- **Git Providers**: GitHub/GitLab for code repos, webhooks for deployment triggers
- **Cloud Provider**: AWS/GCP/Azure for compute, storage, networking services
- **DNS Provider**: Domain management, CNAME verification
- **SSL Authority**: Let's Encrypt for automatic certificate issuance and renewal
- **Add-on Providers**: Third-party services (databases, caching, email, etc.)
- **Payment Processor**: Stripe for billing and payment processing
- **Notification Service**: Email, Slack, webhooks for alerts and notifications

### User Interfaces
- **Web Dashboard**: Application management, deployment history, metrics, billing
- **CLI Tool**: Local development, automation, scripting

## Data Flow Patterns

### Synchronous Request Path
1. User/CLI → API Gateway → Auth Service → Application Service → Database/Cache
2. Response returned directly to user

### Asynchronous Deployment Path
1. Webhook/Manual trigger → Job Queue
2. Build Service picks up job → Builds → Pushes to registry
3. Deploy Service pulls from registry → Creates Kubernetes deployment
4. Status updates published to event bus, users notified

### Observability Path
1. Running containers → Metrics Collector / Log Aggregator
2. Data → Time Series Database / Log Storage
3. Alert Engine continuously evaluates rules
4. Alert fires → Notification Service → Users (email/Slack)

---

**Document Version**: 1.0
**Last Updated**: 2024

## Cross-Phase Traceability Links
- Source requirements: [`../requirements/requirements.md`](../requirements/requirements.md)
- Downstream detailed design: [`../detailed-design/component-diagrams.md`](../detailed-design/component-diagrams.md), [`../detailed-design/sequence-diagrams.md`](../detailed-design/sequence-diagrams.md)
- Implementation execution: [`../implementation/implementation-guidelines.md`](../implementation/implementation-guidelines.md)

