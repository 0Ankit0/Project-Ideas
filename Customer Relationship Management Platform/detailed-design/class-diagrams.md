# Class Diagrams

This document models key domain classes for the CRM bounded context.

## Core Domain Class Model
```mermaid
classDiagram
    class Lead {
      +UUID id
      +LeadStatus status
      +String source
      +Decimal score
      +DateTime createdAt
      +qualify(ownerId)
      +convertToContact(accountId)
      +markDisqualified(reason)
    }

    class Contact {
      +UUID id
      +UUID accountId
      +String email
      +String phone
      +Boolean marketingOptIn
      +mergeFrom(otherContactId)
    }

    class Account {
      +UUID id
      +String name
      +Industry industry
      +UUID territoryId
      +AccountTier tier
      +reassignTerritory(territoryId)
    }

    class Opportunity {
      +UUID id
      +UUID accountId
      +UUID ownerId
      +Stage stage
      +Money amount
      +Date closeDate
      +advanceStage(nextStage)
      +closeWon(actualAmount)
      +closeLost(reason)
    }

    class Activity {
      +UUID id
      +ActivityType type
      +UUID subjectId
      +DateTime scheduledAt
      +DateTime completedAt
      +complete(notes)
      +reschedule(newDateTime)
    }

    class ForecastSnapshot {
      +UUID id
      +YearMonth period
      +UUID ownerScopeId
      +Money commitAmount
      +Money bestCaseAmount
      +SnapshotStatus status
      +submit()
      +approve(approverId)
    }

    class Territory {
      +UUID id
      +String name
      +String regionCode
      +UUID managerId
      +activate()
      +deprecate()
    }

    class MergeCase {
      +UUID id
      +UUID primaryRecordId
      +UUID duplicateRecordId
      +MergeStatus status
      +open()
      +approve(reviewerId)
      +reject(reason)
    }

    Account "1" --> "many" Contact : contains
    Account "1" --> "many" Opportunity : has
    Lead "0..1" --> "1" Contact : converts into
    Opportunity "1" --> "many" Activity : tracked by
    Opportunity "many" --> "1" ForecastSnapshot : rolled into
    Account "many" --> "1" Territory : assigned to
    Lead "0..many" --> "0..many" MergeCase : dedupe review
    Contact "0..many" --> "0..many" MergeCase : dedupe review
```

## Modeling Notes
- Aggregate boundaries are centered on `Lead`, `Account`, `Opportunity`, and `ForecastSnapshot`.
- `MergeCase` supports human-in-the-loop deduplication before irreversible merge operations.
- `Territory` changes are designed to be explicit operations to simplify auditability.

## Domain Glossary
- **Class Responsibility**: File-specific term used to anchor decisions in **Class Diagrams**.
- **Lead**: Prospect record entering qualification and ownership workflows.
- **Opportunity**: Revenue record tracked through pipeline stages and forecast rollups.
- **Correlation ID**: Trace identifier propagated across APIs, queues, and audits for this workflow.

## Entity Lifecycles
- Lifecycle for this document: `Define Class -> Add Behavior -> Validate Associations -> Freeze API`.
- Each transition must capture actor, timestamp, source state, target state, and justification note.

```mermaid
flowchart LR
    A[Define Class] --> B[Add Behavior]
    B[Add Behavior] --> C[Validate Associations]
    C[Validate Associations] --> D[Freeze API]
    D[Freeze API]
```

## Integration Boundaries
- Class boundaries map to domain packages and persistence adapters.
- Data ownership and write authority must be explicit at each handoff boundary.
- Interface changes require schema/version review and downstream impact acknowledgement.

## Error and Retry Behavior
- Serialization failures are non-retryable and logged with schema version.
- Retries must preserve idempotency token and correlation ID context.
- Exhausted retries route to an operational queue with triage metadata.

## Measurable Acceptance Criteria
- Classes expose invariants and cardinality for all associations.
- Observability must publish latency, success rate, and failure-class metrics for this document's scope.
- Quarterly review confirms definitions and diagrams still match production behavior.
