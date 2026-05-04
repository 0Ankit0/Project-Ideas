# Detailed Sequence Diagrams — Customer Relationship Management Platform

## Purpose

These diagrams describe internal service choreography, persistence boundaries, and failure handling for the CRM workflows most likely to create data integrity or cross-system consistency issues.

---

## Sequence 1 — Lead Ingestion, Scoring, and Assignment

```mermaid
sequenceDiagram
    autonumber
    participant Client as Form/API/Import Client
    participant Gateway as API Gateway
    participant LeadSvc as Lead Service
    participant DB as PostgreSQL
    participant Dedupe as Deduplication Engine
    participant Score as Scoring Worker
    participant Assign as Assignment Service
    participant Notify as Notification Service

    Client->>Gateway: Submit lead request
    Gateway->>LeadSvc: Forward validated request
    LeadSvc->>DB: Insert lead
    LeadSvc->>DB: Insert intake row
    LeadSvc->>DB: Insert outbox event
    DB-->>LeadSvc: Commit success
    LeadSvc->>Dedupe: Search duplicate candidates
    alt High confidence duplicate and auto-merge allowed
        Dedupe-->>LeadSvc: Return survivor id
        LeadSvc->>DB: Mark new row merged
    else Manual review or no duplicate
        Dedupe-->>Score: Return candidate result
        Score->>DB: Persist score breakdown
        Score->>Assign: Request assignment
        Assign->>DB: Persist assignment result
        Assign->>DB: Persist SLA timers
        Assign->>Notify: Send owner notification
    end
    LeadSvc-->>Gateway: Lead response resource
    Gateway-->>Client: Return lead response
```

### Implementation Notes
- The initial write is synchronous; scoring and assignment may complete asynchronously but must preserve correlation and causation IDs.
- Deduplication holds row-level locks only for merge execution, not during candidate search.
- Manual review candidates are visible in the UI before assignment if tenant policy requires human approval first.

---

## Sequence 2 — Lead Conversion with Atomic Lineage Creation

```mermaid
sequenceDiagram
    autonumber
    participant UI as Sales UI
    participant Gateway as API Gateway
    participant LeadSvc as Lead Service
    participant AccountSvc as Account Service
    participant ContactSvc as Contact Service
    participant OppSvc as Opportunity Service
    participant DB as PostgreSQL
    participant Bus as Event Bus

    UI->>Gateway: Submit convert command
    Gateway->>LeadSvc: Forward convert command
    LeadSvc->>DB: Lock lead row FOR UPDATE
    LeadSvc->>AccountSvc: Resolve account target
    AccountSvc->>DB: Upsert account
    LeadSvc->>ContactSvc: Create contact
    ContactSvc->>DB: Insert contact
    alt Opportunity requested
        LeadSvc->>OppSvc: Create opportunity
        OppSvc->>DB: Insert opportunity
        OppSvc->>DB: Insert stage history
    end
    LeadSvc->>DB: Update lead status
    LeadSvc->>DB: Update lineage pointers
    LeadSvc->>DB: Insert audit row
    LeadSvc->>DB: Insert outbox events
    DB-->>LeadSvc: Commit transaction
    LeadSvc->>Bus: Publish LeadConverted
    LeadSvc-->>Gateway: Conversion result payload
    Gateway-->>UI: Return conversion result
```

### Failure Handling
- Any failure before commit aborts the entire transaction.
- If event publication fails after commit, the outbox relay retries; the UI still receives success once the DB transaction commits.
- Duplicate conflicts found during account/contact creation return actionable candidate lists rather than partial success.

---

## Sequence 3 — Opportunity Stage Change and Forecast Recalculation

```mermaid
sequenceDiagram
    autonumber
    participant UI as Sales UI
    participant Gateway as API Gateway
    participant OppSvc as Opportunity Service
    participant Policy as Stage Gate Policy Engine
    participant DB as PostgreSQL
    participant Bus as Event Bus
    participant Forecast as Forecast Service
    participant Audit as Audit Service

    UI->>Gateway: Submit stage transition
    Gateway->>OppSvc: Forward transition command
    OppSvc->>Policy: Validate stage rules
    Policy-->>OppSvc: Pass or fail
    OppSvc->>DB: Update opportunity
    OppSvc->>DB: Insert stage history
    OppSvc->>DB: Insert outbox delta event
    DB-->>OppSvc: Commit
    OppSvc->>Bus: Publish OpportunityStageChanged
    Bus->>Forecast: Consume delta event
    Forecast->>DB: Update snapshot lines
    Forecast->>DB: Update rollup aggregates
    alt Period frozen
        Forecast->>DB: Insert forecast exception record only
    end
    Bus->>Audit: Persist immutable transition evidence
    OppSvc-->>Gateway: Updated opportunity view
    Gateway-->>UI: Return updated stage
```

### Integrity Controls
- Forecast recalculation consumes both old and new opportunity values so rollups remain balanced.
- Manager-approved or frozen snapshots are never mutated directly; only exception records are appended.
- A stale version token returns `409 VERSION_CONFLICT` before any state change occurs.

---

## Sequence 4 — Duplicate Review, Merge, and Optional Unmerge

```mermaid
sequenceDiagram
    autonumber
    participant Reviewer as RevOps Reviewer
    participant UI as Admin UI
    participant MergeSvc as Merge Service
    participant DB as PostgreSQL
    participant Search as Search Projection Worker
    participant Bus as Event Bus

    Reviewer->>UI: Open duplicate review queue item
    UI->>MergeSvc: Load merge context
    MergeSvc->>DB: Read candidate rows
    MergeSvc->>DB: Read match reasons
    MergeSvc->>DB: Read relationship counts
    MergeSvc-->>UI: Return comparison view
    MergeSvc-->>UI: Return recommended survivor
    Reviewer->>UI: Submit merge decision
    UI->>MergeSvc: Merge command
    MergeSvc->>DB: Lock both records
    MergeSvc->>DB: Lock relationship rows
    MergeSvc->>DB: Update survivor
    MergeSvc->>DB: Repoint references
    MergeSvc->>DB: Insert merge ledger
    MergeSvc->>DB: Mark source merged
    MergeSvc->>DB: Store source snapshot
    DB-->>MergeSvc: Commit
    MergeSvc->>Bus: Publish RecordMerged
    Bus->>Search: Reindex survivor
    Bus->>Search: Tombstone source
    alt Admin requests unmerge within policy window
        Reviewer->>UI: Start unmerge
        UI->>MergeSvc: Unmerge command
        MergeSvc->>DB: Restore source from snapshot
        MergeSvc->>DB: Repoint reversible links
        MergeSvc->>Bus: Publish RecordUnmerged
    end
```

### Integrity Controls
- Merge execution is pair-locked by sorted record IDs so concurrent merges cannot deadlock unpredictably.
- Non-reversible actions, such as downstream provider deletes, are blocked until the unmerge window closes or tracked separately.
- Consent, legal-hold, and GDPR flags always resolve to the most restrictive effective state on the survivor.

---

## Sequence 5 — Email and Calendar Sync Reconciliation

```mermaid
sequenceDiagram
    autonumber
    participant Provider as Google or Microsoft
    participant Ingress as Integration Webhook Ingress
    participant SyncSvc as Activity Sync Service
    participant Vault as Secret and Token Store
    participant DB as PostgreSQL
    participant Bus as Event Bus
    participant UI as CRM UI

    Provider->>Ingress: Webhook or delta notification
    Ingress->>SyncSvc: Normalized provider event envelope
    SyncSvc->>DB: Check processed-event ledger
    SyncSvc->>DB: Load connection state
    alt Token expired or subscription invalid
        SyncSvc->>Vault: Refresh token
        alt Refresh fails
            SyncSvc->>DB: Mark connection REAUTH_REQUIRED
            SyncSvc->>DB: Record sync error
            SyncSvc->>Bus: Publish sync degraded event
            Bus-->>UI: Surface reconnect banner
        end
    else Event is new
        SyncSvc->>DB: Upsert provider record
        SyncSvc->>DB: Upsert timeline links
        SyncSvc->>DB: Advance cursor
        SyncSvc->>DB: Update replay ledger
        SyncSvc->>Bus: Publish activity-linked event
    end
```

### Integrity Controls
- Provider message IDs and recurrence-instance keys are part of the dedupe ledger.
- Cursor advancement occurs only when the corresponding activity write commits.
- Replay jobs read the same ledger, allowing safe provider reprocessing after outages.

---

## Sequence 6 — Territory Reassignment with Forecast Preservation

```mermaid
sequenceDiagram
    autonumber
    participant RevOps as RevOps Analyst
    participant Territory as Forecast and Territory Service
    participant DB as PostgreSQL
    participant Forecast as Forecast Service
    participant Campaign as Campaign Service
    participant Activity as Activity Service
    participant Notify as Notification Service

    RevOps->>Territory: Submit approved reassignment plan
    Territory->>DB: Create reassignment job
    Territory->>DB: Store impact snapshot
    Territory->>DB: Reassign accounts
    Territory->>DB: Reassign eligible opportunities
    Territory->>Forecast: Rebuild open-period attribution
    Territory->>Campaign: Recalculate future audience
    Territory->>Activity: Repoint open tasks
    Territory->>Activity: Repoint future meetings
    Territory->>Notify: Send old owner notification
    Territory->>Notify: Send new owner notification
    Territory->>DB: Persist reconciliation summary
    Territory->>DB: Persist unresolved conflicts
```

### Integrity Controls
- Historical activities and already-sent campaign analytics stay attached to the pre-change owner for audit truthfulness.
- Future tasks and meetings transfer only when policy says ownership should move with the account.
- Preview and execution both operate from the same normalized rule set and snapshot version.

## Acceptance Criteria

- Each sequence identifies the transaction boundary, async fan-out, and replay surface.
- Failure paths are explicit enough to implement retries, compensations, and operational alerts.
- The diagrams cover CRM-specific risks: lead conversion lineage, forecast freeze, merge auditability, sync replay, and territory reassignment.
