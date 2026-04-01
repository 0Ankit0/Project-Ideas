# High-Level System Design: Sequence Diagrams

## Scenario 1: Complete Deployment from Git Push to Live

This sequence shows the entire flow from a developer pushing code to the application being live and serving traffic.

```mermaid
sequenceDiagram
    participant Developer
    participant GitHub as GitHub<br/>Repository
    participant Webhook as AHP Webhook<br/>Handler
    participant Queue as Job Queue
    participant Builder as Build<br/>Service
    participant Registry as Container<br/>Registry
    participant Deploy as Deploy<br/>Service
    participant K8s as Kubernetes<br/>Cluster
    participant LB as Load<br/>Balancer
    participant App as Running<br/>Application
    participant Monitoring as Metrics &<br/>Logging

    Developer->>GitHub: git push main
    GitHub->>Webhook: Trigger webhook
    Webhook->>Queue: Create build job<br/>(deployment.triggered)
    Queue-->>Webhook: Job queued

    Builder->>Queue: Poll for jobs
    Builder->>GitHub: Clone repo<br/>@ commit SHA
    Builder->>Builder: Analyze project<br/>Detect language
    Builder->>Builder: Execute build<br/>npm install<br/>npm run build

    Builder->>Registry: docker build & push<br/>image:v1.2.3
    Registry-->>Builder: Image stored<br/>image digest

    Deploy->>K8s: Create Deployment<br/>spec with image:v1.2.3
    K8s->>K8s: Schedule Pod<br/>Pull image

    K8s->>Registry: docker pull image:v1.2.3
    K8s->>K8s: Start container<br/>Inject env vars

    K8s->>App: Health check<br/>GET /health
    App-->>K8s: 200 OK

    K8s->>LB: Register instance<br/>behind load balancer

    LB->>App: Test request
    App-->>LB: 200 OK<br/>Response

    Deploy->>Monitoring: Emit event<br/>deployment.succeeded

    Monitoring->>Developer: Send notification<br/>"Deployed successfully"

    Developer->>LB: Visit myapp.ahp.io
    LB->>App: Route request
    App-->>LB: Response
    LB-->>Developer: Rendered page

    par Continuous Operation
        K8s->>Monitoring: Send metrics<br/>CPU, memory, requests
        App->>Monitoring: Stream logs
        LB->>Monitoring: Track latency
    end

    Note over Developer,App: Deployment complete in < 2 minutes
```

**Key Decision Points:**
1. **At GitHub**: Does commit match webhook signature?
2. **At Builder**: Is language detected? Is build successful?
3. **At K8s**: Do health checks pass?
4. **At LB**: Is instance healthy? Route traffic

**Failure Paths:**
- Build fails → Keep old version running, notify developer
- Health check fails → Roll back to previous version, keep serving
- Registry unavailable → Queue retries, other deployments proceed

---

## Scenario 2: Custom Domain with SSL Certificate Provisioning

This sequence shows how a custom domain is connected and HTTPS is automatically provisioned.

```mermaid
sequenceDiagram
    participant Developer
    participant AHP_UI as AHP<br/>Dashboard
    participant DNS_Registrar as Domain<br/>Registrar
    participant DNS_System as DNS<br/>System
    participant LE as Let's<br/>Encrypt
    participant LB as Load<br/>Balancer
    participant Browser as User<br/>Browser

    Developer->>AHP_UI: Add custom domain<br/>myapp.com
    AHP_UI->>AHP_UI: Generate CNAME<br/>myapp.ahp.io
    AHP_UI-->>Developer: Show instructions<br/>Create CNAME record

    Developer->>DNS_Registrar: Login
    DNS_Registrar->>DNS_System: Create CNAME<br/>myapp.com → myapp.ahp.io
    Developer->>AHP_UI: Confirm DNS updated

    AHP_UI->>DNS_System: Query DNS<br/>Resolve CNAME
    DNS_System-->>AHP_UI: CNAME verified ✓

    AHP_UI->>LE: Request certificate<br/>domain: myapp.com
    LE->>AHP_UI: ACME challenge:<br/>Add TXT record

    AHP_UI->>DNS_System: Create TXT record<br/>_acme-challenge.myapp.com

    LE->>DNS_System: Query TXT record<br/>Verify challenge
    DNS_System-->>LE: TXT record found

    LE->>LE: Validate ownership<br/>Issue certificate

    LE-->>AHP_UI: Certificate issued<br/>cert.pem, key.pem

    AHP_UI->>LB: Install certificate<br/>Configure TLS

    LB->>LB: TLS endpoint ready<br/>Port 443

    Browser->>LB: HTTPS request<br/>GET /

    LB->>LB: TLS handshake<br/>Present certificate

    LB->>App: Route to app<br/>in backend

    App-->>LB: Response

    LB-->>Browser: HTTPS response<br/>Valid certificate ✓

    par Auto-Renewal
        AHP_UI->>AHP_UI: Monitor cert<br/>expiration (30 days before)
        AHP_UI->>LE: Request renewal<br/>30 days before expiration
        LE-->>AHP_UI: New certificate<br/>issued
        AHP_UI->>LB: Install new cert<br/>Zero-downtime update
    end

    Note over Developer,LB: HTTPS enabled within 5 minutes
```

**Key Verification Points:**
1. CNAME DNS propagation (poll until confirmed)
2. ACME TXT record ownership verification
3. Certificate installation on load balancer

---

## Scenario 3: Auto-Scaling Based on CPU Threshold

This sequence shows how metrics are collected, evaluated, and auto-scaling is triggered.

```mermaid
sequenceDiagram
    participant App as Running<br/>App Instances
    participant Metrics as Metrics<br/>Collector
    participant TSDB as Time Series<br/>DB
    participant ScaleEngine as Scaling<br/>Engine
    participant K8s as Kubernetes<br/>Orchestrator
    participant LB as Load<br/>Balancer
    participant Notify as Notification<br/>Service
    participant Ops as Ops<br/>Engineer

    par Every 10 seconds
        App->>Metrics: Expose metrics<br/>/metrics (CPU, memory)
        Metrics->>TSDB: Store metrics<br/>timestamp + values
    end

    par Every 60 seconds
        ScaleEngine->>TSDB: Query metrics<br/>Last 5 minutes
        TSDB-->>ScaleEngine: CPU values<br/>[45%, 52%, 68%, 72%, 75%]
    end

    ScaleEngine->>ScaleEngine: Evaluate rules:<br/>avg(CPU) = 62.4%

    ScaleEngine->>ScaleEngine: Check condition:<br/>CPU > 70% for 2 min?<br/>Not yet...

    par Next evaluation (60s later)
        ScaleEngine->>TSDB: Query metrics
        TSDB-->>ScaleEngine: CPU values<br/>[52%, 68%, 72%, 75%, 78%]
        ScaleEngine->>ScaleEngine: avg(CPU) = 69%<br/>Still not > 70%
    end

    par Traffic spike hits
        App->>Metrics: Expose high CPU
        Metrics->>TSDB: [72%, 75%, 78%, 81%, 79%]
    end

    ScaleEngine->>ScaleEngine: avg(CPU) = 77% > 70%<br/>Condition true for 2 min! ✓

    ScaleEngine->>K8s: Scale deployment<br/>replicas: 3 → 5

    K8s->>K8s: Provision 2 new Pods<br/>Pull image

    K8s->>App: Start containers<br/>Inject env vars

    K8s->>App: Health check<br/>GET /health
    App-->>K8s: 200 OK ✓

    K8s->>LB: Register new instances<br/>Add to service endpoint

    LB->>LB: Update routing<br/>Distribute traffic

    ScaleEngine->>Notify: Emit event<br/>scaling.triggered

    Notify->>Ops: Slack message<br/>"Auto-scaled to 5 instances"

    par Metrics return to normal
        App->>Metrics: CPU drops<br/>[45%, 42%, 38%, 35%, 32%]
    end

    ScaleEngine->>ScaleEngine: Cooldown period<br/>5 min (prevent oscillation)
    ScaleEngine->>ScaleEngine: After cooldown:<br/>CPU < 30% for 5 min? Yes!

    ScaleEngine->>K8s: Scale deployment<br/>replicas: 5 → 4

    K8s->>LB: Deregister instance<br/>Graceful drain

    K8s->>K8s: Stop 1 Pod<br/>after 30s timeout

    ScaleEngine->>Notify: Emit event<br/>scaling.triggered

    Notify->>Ops: Slack message<br/>"Auto-scaled down to 4 instances"

    Note over App,LB: Auto-scaling complete in ~2 minutes total
```

**Key Thresholds:**
- Metric collection: 10-second intervals
- Rule evaluation: 60-second intervals
- Duration check: N consecutive true evaluations
- Cooldown: Prevents rapid scale oscillations

---

**Document Version**: 1.0
**Last Updated**: 2024
