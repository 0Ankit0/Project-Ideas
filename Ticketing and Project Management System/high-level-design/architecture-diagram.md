# Architecture Diagram - Ticketing and Project Management System

```mermaid
flowchart TB
    subgraph access[Access Channels]
        cp[Client Portal]
        iw[Internal Workspace]
    end

    subgraph platform[Core Platform]
        gateway[API Gateway]
        iam[Identity and Access]
        ticket[Ticket Service]
        project[Project Service]
        workflow[Workflow and SLA Engine]
        release[Release Service]
        notify[Notification Service]
        report[Reporting and Search]
    end

    subgraph data[Data Layer]
        pg[(PostgreSQL)]
        obj[(Object Storage)]
        idx[(Search Index)]
        mq[(Message Bus)]
    end

    cp --> gateway
    iw --> gateway
    gateway --> iam
    gateway --> ticket
    gateway --> project
    gateway --> release
    ticket --> workflow
    project --> workflow
    ticket --> pg
    project --> pg
    release --> pg
    ticket --> obj
    ticket --> mq
    project --> mq
    release --> mq
    mq --> notify
    mq --> report
    report --> idx
```

## Responsibilities

| Component | Responsibility |
|-----------|----------------|
| Client Portal | External ticket creation and status tracking |
| Internal Workspace | Full operational and project management experience |
| Ticket Service | Ticket lifecycle, comments, attachments, assignment |
| Project Service | Projects, milestones, tasks, change control, health |
| Workflow and SLA Engine | Timers, escalations, status transitions, policy checks |
| Release Service | Planned releases, hotfixes, verification rollups |
| Notification Service | Email, in-app, and chat notifications |
| Reporting and Search | Dashboards, trend analysis, fast filtering |
