# ERD and Database Schema - Ticketing and Project Management System

```mermaid
erDiagram
    ORGANIZATION ||--o{ USER : has
    ORGANIZATION ||--o{ PROJECT : owns
    PROJECT ||--o{ MILESTONE : contains
    MILESTONE ||--o{ TASK : contains
    PROJECT ||--o{ TICKET : scopes
    TICKET ||--o{ TICKET_ATTACHMENT : stores
    TICKET ||--o{ TICKET_COMMENT : records
    TICKET ||--o{ ASSIGNMENT : tracks
    PROJECT ||--o{ RELEASE : plans
    RELEASE }o--o{ TICKET : includes
    USER ||--o{ ASSIGNMENT : receives
    USER ||--o{ AUDIT_LOG : triggers
```

## Table Notes

| Table | Notes |
|-------|-------|
| organizations | Tenant boundary for external clients |
| users | Mixed internal and client identities |
| projects | Delivery initiatives and ownership |
| milestones | Planned checkpoints with baseline and forecast dates |
| tasks | Granular work items under milestones |
| tickets | Incidents, bugs, requests, or change requests |
| ticket_attachments | Attachment metadata referencing object storage |
| assignments | Ownership history and due date tracking |
| releases | Planned or emergency delivery bundles |
| audit_logs | Immutable operational history |
