# Data Flow Diagrams

## End-to-End Data Flow: Code to Running Application

```mermaid
flowchart LR
    A["👨‍💻 Developer<br/>Code Push"] --> B["🐙 GitHub<br/>Repository"]
    B --> C["🔔 Webhook<br/>Event"]
    C --> D["📋 Job<br/>Queue"]
    
    D --> E["🏗️ Build<br/>Service"]
    E --> F["📦 Built<br/>Artifacts"]
    F --> G["🗂️ Container<br/>Registry"]
    
    G --> H["🚀 Deploy<br/>Service"]
    H --> I["☸️ Kubernetes<br/>Cluster"]
    I --> J["🐳 Running<br/>Container"]
    
    J --> K["⚙️ Load<br/>Balancer"]
    K --> L["👥 End<br/>User"]
    
    J --> M["📊 Metrics<br/>Collector"]
    J --> N["📝 Log<br/>Aggregator"]
    
    M --> O["⏰ Time Series<br/>Database"]
    N --> P["🔍 Log<br/>Storage"]
    
    O --> Q["📈 Analytics<br/>Engine"]
    P --> Q
    
    Q --> R["🖥️ AHP<br/>Dashboard"]
    
    R --> L
    R --> A
    
    style A fill:#90EE90
    style J fill:#FFD700
    style L fill:#87CEEB
    style R fill:#4A90E2
```

**Data Flow Steps:**
1. Developer pushes code to GitHub (commit + branch)
2. GitHub sends webhook to AHP
3. AHP enqueues build job
4. Build service clones, builds, creates image
5. Image pushed to registry (artifact storage)
6. Deploy service pulls image, creates deployment
7. Kubernetes schedules and starts container
8. Container serves traffic via load balancer
9. Running container emits metrics and logs
10. Metrics aggregated to time series DB
11. Logs aggregated to log storage
12. Dashboard queries both for visualization
13. Developer and end users access via AHP UI

---

## Application Deployment Cycle (Circular Data Flow)

```mermaid
flowchart TD
    A["Developer<br/>Configuration<br/>App settings<br/>Env variables"] --> B["AHP<br/>Platform"]
    
    B --> C["Build<br/>Configuration<br/>Buildpack<br/>Build commands"]
    C --> D["Build<br/>Service<br/>Compile<br/>Test<br/>Package"]
    D --> E["Build<br/>Artifacts<br/>Container<br/>Image"]
    
    E --> F["Deployment<br/>Service<br/>Schedule<br/>Health check<br/>Traffic routing"]
    F --> G["Running<br/>Application<br/>Processing<br/>Requests"]
    
    G --> H["Operational<br/>Data<br/>Metrics<br/>Logs<br/>Events"]
    
    H --> I["Monitoring &<br/>Alerting<br/>Evaluate rules<br/>Fire alerts"]
    I --> J["Notifications<br/>Email<br/>Slack<br/>Webhook"]
    
    J --> A
    
    A --> K["Custom<br/>Domains &<br/>SSL<br/>Certificate<br/>Management"]
    K --> B
    
    G --> L["Add-on<br/>Services<br/>Database<br/>Cache<br/>Storage"]
    L --> G
    
    style A fill:#4A90E2
    style G fill:#FFD700
    style H fill:#FF6B6B
    style K fill:#27AE60
```

**Cycles:**
1. **Configuration → Build → Deploy → Run**: Application lifecycle
2. **Run → Monitor → Notify → Adjust**: Operational feedback loop
3. **Add-ons ↔ Running App**: Bidirectional data and connection management
4. **Domains/SSL ↔ Platform**: Network-layer configuration

---

## Billing Data Flow (Usage to Invoice)

```mermaid
flowchart TD
    A["Running<br/>Applications"] -->|Emit metrics| B["Metrics<br/>Events<br/>CPU hours<br/>Bandwidth<br/>Storage"]
    
    B -->|Record hourly| C["Usage<br/>Records<br/>Resource type<br/>Quantity<br/>Unit price"]
    
    C -->|Accumulate| D["Monthly<br/>Aggregation<br/>Sum by<br/>resource type<br/>per app"]
    
    D -->|First day<br/>of month| E["Invoice<br/>Generation<br/>Itemize<br/>Apply discounts<br/>Calculate tax"]
    
    E -->|Send| F["Billing<br/>Email<br/>Invoice PDF<br/>Payment link"]
    
    F -->|Customer| G["Payment<br/>Processing<br/>Credit card<br/>Wire transfer"]
    
    G -->|Record| H["Payment<br/>Records<br/>Amount<br/>Timestamp<br/>Method"]
    
    H -->|Update| I["Billing<br/>Account<br/>Balance<br/>Status<br/>Next due date"]
    
    I -->|Status| J["Billing<br/>Dashboard<br/>Usage graph<br/>Invoice history<br/>Payment status"]
    
    J -->|Inform| K["Account<br/>Owner"]
    
    A -.->|New resource| L["Quota<br/>Check<br/>Billing status<br/>Resource limits"]
    L -.->|Block if unpaid| A
    
    style A fill:#FFD700
    style B fill:#FF6B6B
    style J fill:#4A90E2
    style K fill:#87CEEB
```

**Billing Cycle:**
1. **Hourly**: Record resource usage (CPU hours, bandwidth, storage consumed)
2. **Daily**: Accumulate usage to daily total
3. **Monthly**: Generate invoice with line items and tax
4. **Monthly**: Send invoice via email
5. **Ongoing**: Process payments
6. **Real-time**: Block new resources if account is unpaid

---

## Monitoring & Alert Data Flow

```mermaid
flowchart LR
    A["Application<br/>Instance<br/>Running"] -->|Expose /metrics| B["Prometheus<br/>Metrics<br/>Scraper"]
    
    A -->|Stream logs| C["Log<br/>Shipper<br/>Fluent-bit"]
    
    B -->|Store| D["Time Series<br/>Database<br/>Prometheus/<br/>InfluxDB"]
    
    C -->|Store| E["Log<br/>Aggregator<br/>Elasticsearch"]
    
    D -->|Query| F["Alert<br/>Engine<br/>Evaluate rules"]
    
    F -->|Condition met| G["Alert<br/>Fire Event"]
    
    G -->|Route| H["Notification<br/>Channels"]
    
    H -->|Email| I["Email<br/>Service"]
    H -->|Slack| J["Slack<br/>API"]
    H -->|Webhook| K["Custom<br/>Webhook"]
    
    I --> L["On-Call<br/>Engineer"]
    J --> L
    K --> L
    
    D -->|Query time range| M["Dashboard<br/>Renderer"]
    E -->|Query logs| M
    
    M -->|Display| N["AHP UI<br/>Metrics graph<br/>Log viewer"]
    
    N -->|View| L
    
    style A fill:#FFD700
    style F fill:#FF6B6B
    style L fill:#87CEEB
    style N fill:#4A90E2
```

**Observation Paths:**
1. **Metrics Path**: App → Scraper → TSDB → Alert Engine & Dashboard
2. **Logs Path**: App → Shipper → Log Aggregator → Dashboard
3. **Alert Path**: Metrics → Rule Evaluation → Notification → On-Call

---

**Document Version**: 1.0
**Last Updated**: 2024
