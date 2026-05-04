# Swimlane Diagrams — Customer Relationship Management Platform

## Purpose

The following swimlane diagrams model the highest-risk business workflows that cross user roles and service boundaries: lead intake and conversion, forecast submission and freeze, and territory reassignment during an active quarter.

---

## Swimlane 1 — Lead Intake, Qualification, and Conversion

```mermaid
flowchart LR
    subgraph Prospect[Prospect or Source System]
        P1[Submit form, API payload, or CSV row]
        P2[Receive tracking or validation result]
    end

    subgraph Intake[Lead Intake Service]
        I1[Validate schema, consent, captcha, idempotency]
        I2[Persist lead and intake event]
        I3[Run dedupe candidate search]
    end

    subgraph RevOps[RevOps and Data Steward]
        R1[Review medium-confidence duplicate]
        R2[Approve merge or keep separate]
    end

    subgraph Sales[Sales Rep]
        S1[Review score and assignment]
        S2[Qualify lead]
        S3[Run conversion wizard]
    end

    subgraph Core[CRM Core Services]
        C1[Score lead and assign owner or queue]
        C2[Write activity timeline entry]
        C3[Create account, contact, and opportunity]
        C4[Emit LeadConverted lineage event]
    end

    P1 --> I1 --> I2 --> I3
    I1 --> P2
    I3 -->|High confidence| C1
    I3 -->|Medium confidence| R1 --> R2 --> C1
    I3 -->|No match| C1
    C1 --> C2 --> S1 --> S2 --> S3 --> C3 --> C4
```

### Lane Notes

- **Prospect or Source System** owns the original payload, consent checkbox values, and source attribution.
- **Lead Intake Service** performs synchronous validation only; scoring, assignment, and fuzzy dedupe may continue asynchronously but must complete within the SLA defined in FR-004 and FR-005.
- **RevOps** only intervenes when confidence falls into the manual-review band or when merge policy detects conflicting restricted fields.
- **CRM Core Services** must preserve lead-to-contact/account/opportunity lineage to support attribution, dedupe audit, and GDPR investigation.

---

## Swimlane 2 — Forecast Submission, Approval, and Period Freeze

```mermaid
flowchart LR
    subgraph Rep[Sales Rep]
        A1[Review open opportunities in period]
        A2[Adjust commit, best-case, and pipeline call]
        A3[Submit forecast]
    end

    subgraph Opportunity[Opportunity Service]
        B1[Recompute weighted pipeline by owner and period]
        B2[Publish stage or amount deltas]
    end

    subgraph Forecast[Forecast Service]
        C1[Validate snapshot version and freeze window]
        C2[Persist submission and rollup seed]
        C3[Lock submitted snapshot against direct edits]
        C4[Freeze approved snapshot at close cutoff]
    end

    subgraph Manager[Sales Manager]
        D1[Review rep rationale and exception list]
        D2[Approve or request revision]
    end

    subgraph Audit[Finance and Audit]
        E1[Archive immutable period snapshot]
        E2[Export variance and lineage evidence]
    end

    B1 --> B2 --> C1
    A1 --> A2 --> A3 --> C1
    C1 --> C2 --> C3 --> D1 --> D2
    D2 -->|Approve| C4 --> E1 --> E2
    D2 -->|Request revision| A2
```

### Lane Notes

- Forecast calculations must reference a specific opportunity version set; manager approval cannot silently pick up later stage changes.
- Freeze rules differ by tenant fiscal policy, but once a snapshot is frozen only approved override workflows may reopen it.
- Audit exports must include who submitted, who approved, which opportunities were included, and any manual adjustment reason codes.

---

## Swimlane 3 — Mid-Cycle Territory Reassignment

```mermaid
flowchart LR
    subgraph RevOps2[RevOps Analyst]
        T1[Upload or model reassignment plan]
        T2[Preview impacted accounts and opportunities]
        T3[Approve effective date]
    end

    subgraph Territory[Territory Service]
        U1[Evaluate rules and create reassignment job]
        U2[Snapshot pre-change ownership and quota attribution]
        U3[Reassign accounts and open opportunities]
        U4[Emit downstream repair tasks]
    end

    subgraph Managers[Old and New Managers]
        V1[Review conflict report]
        V2[Confirm split-credit exceptions]
    end

    subgraph Sellers2[Sales Reps]
        W1[Receive ownership change notification]
        W2[Review task, meeting, and campaign impact]
    end

    subgraph Supporting[Forecast, Campaign, and Sync Services]
        X1[Rebuild forecast ownership snapshots]
        X2[Repoint future tasks and meeting attendees]
        X3[Keep sent campaigns on historical owner]
    end

    T1 --> T2 --> U1 --> U2 --> V1 --> V2 --> T3 --> U3 --> U4
    U4 --> W1 --> W2
    U4 --> X1
    U4 --> X2
    U4 --> X3
```

### Lane Notes

- Territory jobs are staged: preview, approval, execution, and reconciliation.
- Forecast ownership for already-frozen periods must remain historical, while open periods can be recalculated according to tenant policy.
- Reassignment must distinguish open future work from historical activity so the timeline remains truthful and auditable.

## Acceptance Criteria

- Each swimlane names the human decision points, automated services, and downstream side effects required for implementation.
- Handoffs include enough detail to derive job orchestration, notification rules, and rollback strategy.
- The diagrams cover the CRM-specific themes of lead conversion, forecast lock/freeze, and territory reassignment impacts.
