# Deployment Diagram - Library Management System

```mermaid
flowchart TB
    internet[Patron Internet Access] --> edge[WAF / CDN]
    staffNet[Branch or Corporate Network] --> internalLb[Internal Access Gateway]
    edge --> patronWeb[Patron Portal Frontend]
    internalLb --> staffWeb[Staff Workspace Frontend]
    patronWeb --> api[Application API Cluster]
    staffWeb --> api
    api --> workers[Background Worker Cluster]
    api --> db[(Managed PostgreSQL)]
    api --> search[(Search Cluster)]
    api --> queue[(Managed Queue / Bus)]
    api --> object[(Object Storage)]
    workers --> db
    workers --> queue
    workers --> object
```

## Deployment Notes
- Patron and staff interfaces are separated at the edge even when they share backend services.
- Background workers handle notifications, fine assessment jobs, search projection, and batch inventory tasks.
- Search infrastructure should be isolated from primary write workloads to preserve transaction stability.
