# Data Flow Diagram - Ticketing and Project Management System

```mermaid
flowchart LR
    client[Client Requester] --> portal[Client Portal]
    internal[Internal Workspace Users] --> workspace[Internal Workspace]
    portal --> api[Application API]
    workspace --> api
    api --> ticketSvc[Ticket Service]
    api --> projectSvc[Project Service]
    api --> attachSvc[Attachment Service]
    ticketSvc --> db[(PostgreSQL)]
    projectSvc --> db
    attachSvc --> object[(Object Storage)]
    ticketSvc --> bus[(Event Bus)]
    projectSvc --> bus
    bus --> notify[Notification Service]
    bus --> report[Reporting / Search]
    report --> search[(Search Index)]
    notify --> email[Email / Chat]
```

## Data Flow Notes

1. Client and internal entry points use different interfaces but the same application API.
2. Ticket and project services publish events for dashboards, notifications, and search indexing.
3. Attachments are stored outside the transactional database and referenced through metadata records.
