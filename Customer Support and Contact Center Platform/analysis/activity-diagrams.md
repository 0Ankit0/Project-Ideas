# Activity Diagrams

## Ticket Intake and Routing
```mermaid
flowchart TD
    A[Customer submits issue] --> B[Validate channel payload]
    B --> C[Classify intent and priority]
    C --> D{Known customer/account?}
    D -- No --> E[Create provisional profile]
    D -- Yes --> F[Attach account context]
    E --> G[Create ticket]
    F --> G
    G --> H[Run routing rules]
    H --> I[Assign queue/agent]
    I --> J[Start SLA timers]
```

## Live Interaction Handling
```mermaid
flowchart TD
    A[Session connected] --> B[Authenticate customer]
    B --> C[Fetch customer history]
    C --> D{Can resolve in L1?}
    D -- Yes --> E[Provide resolution]
    D -- No --> F[Escalate to specialist]
    F --> G[Transfer context and transcript]
    G --> H[Specialist resolves]
    E --> I[Capture disposition]
    H --> I
    I --> J[Close session/ticket]
```

## SLA Breach Management
```mermaid
flowchart TD
    A[SLA monitor tick] --> B[Find at-risk tickets]
    B --> C{Breach imminent?}
    C -- No --> D[No action]
    C -- Yes --> E[Notify supervisor]
    E --> F[Re-prioritize queue]
    F --> G[Reassign to available agent]
```

## Operational Activity Deep Dive
This activity view expands the intake-to-resolution path with explicit queue transitions, SLA clocks, and incident controls so timing and ownership are observable at every step.

```mermaid
flowchart TD
    A[Inbound Event] --> B[Identity Resolution]
    B --> C{Thread Exists?}
    C -- yes --> D[Attach to Active Case]
    C -- no --> E[Create Case + Queue Ticket]
    D --> F[Skill Routing]
    E --> F
    F --> G[Agent Accept]
    G --> H{Needs Escalation?}
    H -- no --> I[Resolve + QA Sampling]
    H -- yes --> J[L2/L3 Escalation]
    J --> K[Escalation Ack SLA]
    K --> I
    I --> L[Audit Ledger + Retention Tags]
```

- **Workflow modeling:** `queued -> assigned -> in_progress -> pending_external -> resolved -> closed` with allowed re-open via policy rule.
- **SLA rules:** first response timer starts at queue entry; resolution timer pauses only in `pending_external` with reason code.
- **Omnichannel handling:** voice/chat/email events normalized into `interaction_event` to keep activity diagrams channel-agnostic.
- **Auditability:** each action step emits `activity_transitioned` with actor, queue, and prior state hash.
- **Incident response:** if routing latency p95 breaches threshold for 5 minutes, fail over to deterministic fallback queue map.
