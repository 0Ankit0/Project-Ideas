# System Sequence Diagrams — Customer Relationship Management Platform

## Purpose

These sequences describe black-box interactions between users or external systems and the CRM platform for the most important end-user workflows.

---

## SSD-01 — Capture and Route Lead

```mermaid
sequenceDiagram
    autonumber
    actor Source as Prospect or Source System
    participant CRM as CRM Platform
    actor Rep as Sales Rep

    Source->>CRM: Submit lead request
    CRM->>CRM: Resolve tenant
    CRM->>CRM: Validate schema
    CRM->>CRM: Validate consent
    CRM->>CRM: Check idempotency
    CRM->>CRM: Persist lead
    CRM->>CRM: Persist intake event
    CRM->>CRM: Calculate score
    CRM->>CRM: Search duplicates
    CRM->>CRM: Evaluate assignment
    alt Lead accepted
        CRM-->>Source: Return acceptance result
        CRM-->>Rep: Send assignment notification
    else Validation or abuse failure
        CRM-->>Source: Return error response
    end
```

---

## SSD-02 — Convert Lead to Customer Records

```mermaid
sequenceDiagram
    autonumber
    actor Rep as Sales Rep
    participant CRM as CRM Platform

    Rep->>CRM: Open Convert Lead wizard
    CRM-->>Rep: Show duplicate candidates
    CRM-->>Rep: Show account options
    CRM-->>Rep: Show field mappings
    Rep->>CRM: Confirm conversion choices
    CRM->>CRM: Validate permissions
    CRM->>CRM: Validate field mappings
    CRM->>CRM: Validate duplicate locks
    CRM->>CRM: Create account
    CRM->>CRM: Create contact
    CRM->>CRM: Create optional opportunity
    CRM->>CRM: Write lead lineage
    CRM-->>Rep: Return created resources
```

---

## SSD-03 — Submit and Approve Forecast

```mermaid
sequenceDiagram
    autonumber
    actor Rep as Sales Rep
    actor Manager as Sales Manager
    participant CRM as CRM Platform

    Rep->>CRM: Open forecast workspace for fiscal period
    CRM-->>Rep: Return derived snapshot
    CRM-->>Rep: Return exception list
    CRM-->>Rep: Return current status
    Rep->>CRM: Submit forecast values
    Rep->>CRM: Submit rationale
    CRM->>CRM: Lock submitted snapshot
    CRM->>CRM: Build rollup delta
    CRM-->>Manager: Send review request
    alt Manager approves
        Manager->>CRM: Approve snapshot
        CRM->>CRM: Freeze approval state
        CRM->>CRM: Update rollup hierarchy
        CRM-->>Rep: Approval confirmation
    else Manager requests revision
        Manager->>CRM: Request revision
        CRM-->>Rep: Revision required notification
    end
```

---

## SSD-04 — Connect Email and Calendar Sync

```mermaid
sequenceDiagram
    autonumber
    actor User as Sales Rep
    participant CRM as CRM Platform
    participant Provider as Google or Microsoft

    User->>CRM: Start sync connection
    CRM-->>User: Redirect to OAuth consent screen
    User->>Provider: Grant scopes
    Provider-->>CRM: Return authorization code
    CRM->>CRM: Store encrypted tokens
    CRM->>CRM: Initialize sync cursor
    CRM-->>User: Return connection status
    Provider-->>CRM: Send provider event
    CRM->>CRM: Dedupe provider event
    CRM->>CRM: Link related records
    CRM->>CRM: Update timeline
```

---

## SSD-05 — Territory Reassignment Preview and Commit

```mermaid
sequenceDiagram
    autonumber
    actor RevOps as RevOps Analyst
    actor Manager as Sales Manager
    participant CRM as CRM Platform

    RevOps->>CRM: Upload reassignment plan
    CRM->>CRM: Evaluate impacted accounts
    CRM->>CRM: Evaluate impacted opportunities
    CRM->>CRM: Evaluate forecast impact
    CRM->>CRM: Evaluate task impact
    CRM-->>RevOps: Return preview counts
    CRM-->>RevOps: Return conflicts
    CRM-->>RevOps: Return quota movement
    RevOps->>CRM: Submit plan for approval
    Manager->>CRM: Approve effective date
    Manager->>CRM: Approve exception policy
    CRM->>CRM: Execute reassignment job
    CRM->>CRM: Queue downstream repairs
    CRM-->>RevOps: Return success count
    CRM-->>RevOps: Return manual review count
```

## Acceptance Criteria

- Each sequence includes user intent, system validations, and visible outcomes.
- Alternate paths cover rejection, revision, or degraded external provider behavior where relevant.
- The sequences are detailed enough to derive API contract tests and end-to-end acceptance tests.
