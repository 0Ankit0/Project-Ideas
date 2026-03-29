# Deployment Diagram - Learning Management System

```mermaid
flowchart TB
    internet[Internet / Learners] --> edge[WAF / CDN]
    staffNet[Staff / Admin Network] --> internalAccess[Internal Access Gateway]
    edge --> learnerWeb[Learner Portal Frontend]
    internalAccess --> staffWeb[Staff Workspace Frontend]
    learnerWeb --> api[Application API Cluster]
    staffWeb --> api
    api --> workers[Background Worker Cluster]
    api --> db[(Managed PostgreSQL)]
    api --> search[(Search / Analytics Cluster)]
    api --> queue[(Managed Queue / Bus)]
    api --> object[(Object Storage / CDN Origin)]
    workers --> db
    workers --> queue
    workers --> object
```

## Deployment Notes

- Learner and staff experiences should be separated at the edge but can share the same core backend platform.
- Background workers handle notifications, progress aggregation, grading queues, certificate issuance, and projection updates.
- Media content and downloadable learning assets should use object storage plus CDN distribution.

## Implementation Details: Deployment Runbook

### Rollout strategy
- API and worker clusters deploy independently with canary + automatic rollback on SLO breach.
- Drain queue consumers before worker replacement to avoid duplicate job execution.

### Environment parity requirements
- Staging mirrors production queue topology and scaling policy.
- DR environment validates restore for transcript, grades, and certificate evidence.
