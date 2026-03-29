# State Machine Diagram - Anomaly Detection System

## 1. Anomaly Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Detected: Score > Threshold
    Detected --> AlertSent: Alert Triggered
    AlertSent --> Acknowledged: Operator ACK
    AlertSent --> Escalated: No ACK (timeout)
    AlertSent --> Suppressed: Suppression Rule
    
    Acknowledged --> Resolved: Issue Fixed
    Acknowledged --> FalsePositive: Marked False
    Escalated --> Acknowledged: Higher Level ACK
    
    Resolved --> [*]
    FalsePositive --> Learning: Feedback Stored
    Learning --> [*]
    Suppressed --> [*]
```

## 2. ML Model Lifecycle

```mermaid
stateDiagram-v2
    [*] --> Training: Start Training
    Training --> Evaluating: Training Complete
    Evaluating --> Registered: Metrics Pass
    Evaluating --> Failed: Metrics Fail
    
    Failed --> Training: Adjust Params
    
    Registered --> Staging: Deploy to Test
    Staging --> Production: A/B Test Pass
    Staging --> Registered: Test Fail
    
    Production --> Monitoring: Active
    Monitoring --> Deprecated: New Model Deployed
    Monitoring --> Retraining: Drift Detected
    
    Retraining --> Training
    Deprecated --> [*]
```

## 3. Alert Status

```mermaid
stateDiagram-v2
    [*] --> Pending: Alert Created
    Pending --> Sent: Delivery Success
    Pending --> Failed: Delivery Failed
    
    Failed --> Pending: Retry
    Failed --> [*]: Max Retries
    
    Sent --> Acknowledged: User ACK
    Sent --> Escalated: Timeout
    Sent --> Suppressed: Quiet Hours
    
    Acknowledged --> Resolved: Closed
    Escalated --> Acknowledged: Higher ACK
    Suppressed --> [*]
    
    Resolved --> [*]
```

## 4. Data Source Status

```mermaid
stateDiagram-v2
    [*] --> Configured: Source Added
    Configured --> Active: Connection Success
    Configured --> Error: Connection Failed
    
    Active --> Streaming: Data Flowing
    Streaming --> Stale: No Data (timeout)
    Streaming --> Error: Stream Error
    
    Stale --> Streaming: Data Resumed
    Stale --> Inactive: Extended Silence
    
    Error --> Active: Retry Success
    Error --> Inactive: Max Retries
    
    Inactive --> [*]: Source Removed
```

## Purpose and Scope
Defines alert and case state transitions, timers, and forbidden paths.

## Assumptions and Constraints
- All transitions are event-driven and auditable.
- Timer events are persisted and replay-safe.
- Forbidden transitions are enforced in code and DB constraints.

### End-to-End Example with Realistic Data
`AL-8831` transitions `New->Triaged->Investigating->Resolved`; if no action for 15 minutes, timer emits `Escalate` leading to `Escalated` state and on-call page.

## Decision Rationale and Alternatives Considered
- Modeled reopen path explicitly to avoid ad-hoc manual edits.
- Rejected implicit “any-to-any” transitions due audit risk.
- Added timeout-triggered escalation for operational safety.

## Failure Modes and Recovery Behaviors
- Timer service delay -> reconciliation worker replays pending timers from durable store.
- Out-of-order transition event -> ignored with conflict audit entry.

## Security and Compliance Implications
- State changes that expose evidence require privileged role check.
- All transition events include actor/service identity.

## Operational Runbooks and Observability Notes
- State stuck-duration metric alerts workflow owner.
- Runbook includes manual transition repair with audit annotation.
