# Deployment Diagram - Ticketing and Project Management System

```mermaid
flowchart TB
    internet[Internet / Client Network] --> waf[WAF / CDN]
    corp[Corporate Network / VPN] --> internalLb[Internal Load Balancer]
    waf --> clientWeb[Client Portal Frontend]
    internalLb --> internalWeb[Internal Workspace Frontend]
    clientWeb --> api[Application API Cluster]
    internalWeb --> api
    api --> worker[Workflow Worker Cluster]
    api --> db[(Managed PostgreSQL)]
    api --> obj[(Object Storage)]
    api --> bus[(Managed Queue / Bus)]
    worker --> db
    worker --> bus
```

## Deployment Notes
- Client-facing and internal frontends are separated at the edge even when they share backend services.
- Workers handle asynchronous scanning, notifications, SLA timers, and report projection.
- Object storage is required for evidence files and exported reports.
