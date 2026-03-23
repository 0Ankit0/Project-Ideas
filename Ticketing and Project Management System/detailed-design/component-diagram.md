# Component Diagram - Ticketing and Project Management System

```mermaid
flowchart LR
    ui[Client Portal / Internal Workspace] --> api[API Layer]
    api --> auth[Access Control Component]
    api --> tickets[Ticket Management Component]
    api --> projects[Project Planning Component]
    api --> releases[Release and Verification Component]
    api --> reports[Reporting Component]
    tickets --> workflow[SLA and Workflow Component]
    tickets --> attachments[Attachment Component]
    projects --> workflow
    releases --> workflow
```

## Component Responsibilities

| Component | Responsibility |
|-----------|----------------|
| Access Control | Authentication, scope checks, role evaluation |
| Ticket Management | Ticket CRUD, comments, history, duplicate detection |
| Attachment | Upload validation, scanning, secure retrieval |
| Project Planning | Projects, milestones, tasks, dependency tracking |
| SLA and Workflow | Timers, escalations, status transitions |
| Release and Verification | Release grouping, QA outcomes, hotfix support |
| Reporting | Dashboards, metrics, filters, exports |
