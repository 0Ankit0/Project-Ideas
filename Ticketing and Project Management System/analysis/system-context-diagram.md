# System Context Diagram - Ticketing and Project Management System

```mermaid
flowchart LR
    clientOrg[Client Organization Users]
    internalTeams[Internal Support, PM, Dev, QA, Admin]
    idp[Identity Provider / SSO]
    mail[Email and Chat Notification Services]
    scm[Source Control / CI-CD]
    storage[Object Storage + Malware Scan]

    subgraph tpm[Ticketing and Project Management System]
        portal[Client Portal]
        workspace[Internal Workspace]
        api[Application API]
        search[Search and Reporting]
    end

    clientOrg --> portal
    internalTeams --> workspace
    portal --> api
    workspace --> api
    api --> idp
    api --> storage
    api --> mail
    api --> scm
    api --> search
```

## Context Notes

- Client users only access the client portal and records scoped to their organization.
- Internal teams use the internal workspace for triage, planning, delivery, verification, and administration.
- The platform integrates with SSO, notifications, source control, and secure object storage.
