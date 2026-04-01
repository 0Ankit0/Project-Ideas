# Swimlane Diagrams: Cross-Functional Workflows

Swimlane diagrams show how different actors and systems interact across business processes.

## 1. Application Deployment Pipeline (Developer → Production)

```mermaid
flowchart TD
    Developer["Developer"]
    AHP_UI["AHP Platform"]
    Git["Git Provider<br/>GitHub/GitLab"]
    BuildService["Build Service"]
    Registry["Container Registry"]
    DeployService["Deploy Service"]
    K8s["Kubernetes Cluster"]
    LB["Load Balancer"]
    CDN["CDN"]
    
    Developer -->|1. Git Push| Git
    Git -->|2. Webhook| AHP_UI
    AHP_UI -->|3. Clone Repo| Git
    AHP_UI -->|4. Start Build| BuildService
    
    BuildService -->|5. Fetch Code| Git
    BuildService -->|6. Execute Build<br/>npm install<br/>npm run build| BuildService
    BuildService -->|7. Create Image| BuildService
    BuildService -->|8. Push Image| Registry
    
    AHP_UI -->|9. Pull Image| Registry
    AHP_UI -->|10. Create Deployment| DeployService
    
    DeployService -->|11. Schedule Pod| K8s
    K8s -->|12. Pull Image| Registry
    K8s -->|13. Start Container| K8s
    K8s -->|14. Run Health Check| K8s
    
    K8s -->|15. Register Instance| LB
    LB -->|16. Route Traffic| K8s
    K8s -->|17. Serve Traffic| LB
    LB -->|18. Cache & Distribute| CDN
    
    K8s -->|19. Stream Metrics| AHP_UI
    K8s -->|19b. Stream Logs| AHP_UI
    
    AHP_UI -->|20. Deployment Successful| Developer
    Developer -->|21. Verify Live| LB
    
    style Developer fill:#90EE90
    style AHP_UI fill:#4A90E2
    style Git fill:#333
    style BuildService fill:#FFD700
    style DeployService fill:#FF6B6B
    style K8s fill:#9B59B6
    style LB fill:#FF9900
    style CDN fill:#00CED1
```

**Swimlanes (Actors/Systems):**
1. **Developer**: Initiates deployment via git push
2. **Git Provider**: Hosts code, sends webhook
3. **AHP Platform**: Orchestrates entire flow
4. **Build Service**: Compiles and creates container image
5. **Container Registry**: Stores container images
6. **Deploy Service**: Manages Kubernetes deployments
7. **Kubernetes Cluster**: Runs containers, health checks
8. **Load Balancer**: Routes traffic to instances
9. **CDN**: Caches static content globally

**Key Handoff Points:**
- Git webhook to AHP (automation trigger)
- Build service to registry (artifact storage)
- Kubernetes to load balancer (traffic routing)
- Running app to AHP (metrics/logs collection)

---

## 2. Custom Domain Setup with SSL (Multi-Party)

```mermaid
flowchart TD
    Developer["Developer"]
    AHP_Dashboard["AHP Dashboard"]
    DNS_Registrar["Domain Registrar<br/>(GoDaddy, AWS Route53)"]
    DNS_System["DNS System"]
    LE["Let's Encrypt<br/>Certificate Authority"]
    LB["Load Balancer<br/>TLS Endpoint"]
    
    Developer -->|1. Add Domain<br/>myapp.com| AHP_Dashboard
    AHP_Dashboard -->|2. Generate<br/>CNAME Target| AHP_Dashboard
    AHP_Dashboard -->|3. Show Instructions<br/>Create CNAME:<br/>myapp.com → myapp.ahp.io| Developer
    
    Developer -->|4. Login| DNS_Registrar
    DNS_Registrar -->|5. Update CNAME<br/>Record| DNS_System
    Developer -->|6. Confirm in AHP| AHP_Dashboard
    
    AHP_Dashboard -->|7. Poll DNS<br/>Query CNAME| DNS_System
    DNS_System -->|8. Return CNAME| AHP_Dashboard
    AHP_Dashboard -->|9. CNAME Verified| AHP_Dashboard
    
    AHP_Dashboard -->|10. Request<br/>Certificate| LE
    LE -->|11. DNS Challenge<br/>Add TXT Record| DNS_System
    AHP_Dashboard -->|12. Update TXT<br/>Record| DNS_System
    
    LE -->|13. Verify Domain<br/>Query TXT Record| DNS_System
    DNS_System -->|14. Return TXT| LE
    LE -->|15. Issue Certificate<br/>cert.pem, key.pem| AHP_Dashboard
    
    AHP_Dashboard -->|16. Install Cert<br/>on Load Balancer| LB
    LB -->|17. Configure TLS<br/>myapp.com → cert| LB
    
    AHP_Dashboard -->|18. Verify HTTPS<br/>curl https://myapp.com| LB
    LB -->|19. HTTPS Response| AHP_Dashboard
    AHP_Dashboard -->|20. Domain Active!| Developer
    
    Developer -->|21. Confirm Production| Developer
    Developer -->|22. Visit myapp.com| LB
    LB -->|23. Serve HTTPS<br/>with Certificate| Developer
    
    style Developer fill:#90EE90
    style AHP_Dashboard fill:#4A90E2
    style DNS_Registrar fill:#1E90FF
    style LE fill:#27AE60
    style LB fill:#FF9900
    style DNS_System fill:#1E90FF
```

**Swimlanes:**
1. **Developer**: Creates domain entry, updates DNS registrar
2. **AHP Dashboard**: Orchestrates domain setup and verification
3. **Domain Registrar**: Stores CNAME/DNS records
4. **DNS System**: Resolves domain names globally
5. **Let's Encrypt**: Issues SSL certificates via ACME
6. **Load Balancer**: Terminates TLS, serves HTTPS

**Critical Handoff Points:**
- DNS CNAME creation and verification
- Certificate issuance from Let's Encrypt
- TLS configuration on load balancer

---

## 3. Alert Detection & Notification (Ops Engineer)

```mermaid
flowchart TD
    K8s_Cluster["Kubernetes Cluster<br/>(Running App)"]
    Metrics_Collector["Metrics Collector"]
    TimeSeries_DB["Time Series Database<br/>Prometheus"]
    Alert_Engine["Alert Engine"]
    AHP_API["AHP API"]
    Notification["Notification Service"]
    Email["Email Service"]
    Slack["Slack API"]
    Engineer["Operations<br/>Engineer"]
    AHP_UI["AHP Dashboard"]
    
    K8s_Cluster -->|1. Expose Metrics<br/>/metrics endpoint| Metrics_Collector
    Metrics_Collector -->|2. Scrape Every<br/>10 Seconds| K8s_Cluster
    Metrics_Collector -->|3. Store Metrics<br/>CPU, Memory<br/>Request Rate| TimeSeries_DB
    
    Alert_Engine -->|4. Query Metrics<br/>Every 60 Seconds| TimeSeries_DB
    TimeSeries_DB -->|5. Return<br/>Metric Values| Alert_Engine
    
    Alert_Engine -->|6. Evaluate<br/>Rules| Alert_Engine
    Alert_Engine -->|7. Check<br/>Condition<br/>error_rate > 5%<br/>for 5 min| Alert_Engine
    
    Alert_Engine -->|8. Condition Met<br/>Alert Fires| Notification
    Notification -->|9. Format Alert<br/>Message| Notification
    Notification -->|10. Send Email| Email
    Notification -->|11. Send to Slack<br/>#alerts| Slack
    
    Email -->|12. Deliver Email| Engineer
    Slack -->|13. Post Message| Engineer
    
    Engineer -->|14. Click Alert Link| AHP_UI
    AHP_UI -->|15. Get Alert<br/>Details| AHP_API
    AHP_API -->|16. Load Metrics<br/>Graph| TimeSeries_DB
    AHP_UI -->|17. Display Graph<br/>+ Logs| Engineer
    
    Engineer -->|18. Investigate<br/>Issue| Engineer
    Engineer -->|19. Fix Issue| Engineer
    Engineer -->|20. Acknowledge Alert| AHP_UI
    AHP_UI -->|21. Mark Alert<br/>Acknowledged| AHP_API
    
    Alert_Engine -->|22. Condition<br/>Resolves<br/>error_rate drops| Alert_Engine
    Alert_Engine -->|23. Alert Cleared| Notification
    Notification -->|24. Send<br/>Resolved Email| Email
    Notification -->|25. Post Resolved<br/>Message| Slack
    
    Email -->|26. Deliver Email| Engineer
    Slack -->|27. Post Message| Engineer
    
    style K8s_Cluster fill:#9B59B6
    style Alert_Engine fill:#FF6B6B
    style Engineer fill:#90EE90
    style AHP_UI fill:#4A90E2
    style Notification fill:#FFD700
    style Metrics_Collector fill:#00CED1
    style TimeSeries_DB fill:#FF9900
```

**Swimlanes:**
1. **Kubernetes Cluster**: Emits metrics from running application
2. **Metrics Collector**: Scrapes and collects metrics
3. **Time Series Database**: Stores metrics with timestamps
4. **Alert Engine**: Evaluates rules and fires alerts
5. **Notification Service**: Routes alerts to channels
6. **Email & Slack**: Deliver notifications
7. **Operations Engineer**: Receives alert, investigates, responds

**Critical Paths:**
- Metric collection (every 10 seconds)
- Alert evaluation (every 60 seconds)
- Notification delivery (immediate)
- Resolution detection (automatic when condition clears)

---

**Document Version**: 1.0
**Last Updated**: 2024
