# Event Catalog - Ticketing and Project Management System

| Event | Producer | Consumers | Description |
|-------|----------|-----------|-------------|
| ticket.created | Client Portal / API | Triage Queue, Notification Service | New issue reported |
| attachment.scanned | Attachment Service | Ticket Service | Evidence upload completed or quarantined |
| ticket.triaged | Triage Service | Assignment Engine, Reporting | Category, priority, and SLA set |
| ticket.assigned | Assignment Engine | Notification Service, Work Queue | Ownership updated |
| ticket.blocked | Developer Workflow | Project Service, Reporting | Work blocked and risk exposed |
| ticket.ready_for_qa | Ticket Service | QA Queue | Development completed |
| ticket.reopened | QA Workflow | Developer Queue, Notification Service | Fix failed verification |
| ticket.closed | QA Workflow | Client Portal, Reporting | Verification passed and work finished |
| project.created | Project Service | Reporting, Notification Service | New delivery initiative started |
| milestone.baselined | Project Service | Reporting, Dashboard | Planned checkpoint approved |
| milestone.forecast_changed | Project Service | PM Dashboard, Notification Service | Delivery date moved |
| change_request.created | Ticket or Project Service | PM Approval Queue | Scope change requires review |
| release.planned | Release Service | QA Queue, Notification Service | Deployment scheduled |
| release.deployed | Release Service | Ticket Service, Reporting | Release completed |
| admin.policy_changed | Admin Service | Audit Service | Workflow or SLA rule changed |
