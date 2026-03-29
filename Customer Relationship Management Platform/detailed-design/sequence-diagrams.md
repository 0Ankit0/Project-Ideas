# Sequence Diagrams

## Lead Creation and Deduplication
```mermaid
sequenceDiagram
    autonumber
    participant U as User/Integration
    participant API as CRM API
    participant Lead as Lead Service
    participant Dup as Dedup Service
    participant DB as DB
    participant Q as Review Queue

    U->>API: POST /v1/leads
    API->>Lead: validate + map request
    Lead->>Dup: findCandidates(email, phone, company)
    alt Candidate found
      Dup-->>Lead: duplicate matches
      Lead->>DB: create lead(status=NeedsReview)
      Lead->>Q: enqueue merge review case
      Lead-->>API: 202 Accepted (review pending)
    else No candidate
      Dup-->>Lead: no matches
      Lead->>DB: create lead(status=New)
      Lead-->>API: 201 Created
    end
```

## Opportunity Stage Transition
```mermaid
sequenceDiagram
    autonumber
    participant Rep as Sales Rep
    participant BFF as BFF
    participant Opp as Opportunity Service
    participant Policy as Policy Engine
    participant Audit as Audit Log
    participant Bus as Event Bus

    Rep->>BFF: move stage to Proposal
    BFF->>Opp: transition(opportunityId, Proposal)
    Opp->>Policy: authorize + validate guards
    Policy-->>Opp: allowed
    Opp->>Audit: append stage-change audit
    Opp->>Bus: publish OpportunityStageChanged
    Opp-->>BFF: updated opportunity
    BFF-->>Rep: success
```

## Domain Glossary
- **Message Exchange**: File-specific term used to anchor decisions in **Sequence Diagrams**.
- **Lead**: Prospect record entering qualification and ownership workflows.
- **Opportunity**: Revenue record tracked through pipeline stages and forecast rollups.
- **Correlation ID**: Trace identifier propagated across APIs, queues, and audits for this workflow.

## Entity Lifecycles
- Lifecycle for this document: `Caller Sends -> Service Validates -> DB Commit -> Event Publish -> Ack`.
- Each transition must capture actor, timestamp, source state, target state, and justification note.

```mermaid
flowchart LR
    A[Caller Sends] --> B[Service Validates]
    B[Service Validates] --> C[DB Commit]
    C[DB Commit] --> D[Event Publish]
    D[Event Publish] --> E[Ack]
    E[Ack]
```

## Integration Boundaries
- Sequences show synchronous call edges and async fanout edges.
- Data ownership and write authority must be explicit at each handoff boundary.
- Interface changes require schema/version review and downstream impact acknowledgement.

## Error and Retry Behavior
- Each sequence shows timeout and compensating branch for failed downstream step.
- Retries must preserve idempotency token and correlation ID context.
- Exhausted retries route to an operational queue with triage metadata.

## Measurable Acceptance Criteria
- Correlation ID is present at every hop in sequence annotations.
- Observability must publish latency, success rate, and failure-class metrics for this document's scope.
- Quarterly review confirms definitions and diagrams still match production behavior.
