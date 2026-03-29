# State Machine Diagram - Backend as a Service Platform

## Capability Binding Lifecycle

```mermaid
stateDiagram-v2
    [*] --> draft
    draft --> validating
    validating --> active
    validating --> failed_validation
    active --> migrating
    migrating --> cutover_pending
    cutover_pending --> active_target
    cutover_pending --> rollback_pending
    rollback_pending --> active
    active_target --> deprecated_source
    deprecated_source --> retired
```

## Function Deployment Lifecycle

```mermaid
stateDiagram-v2
    [*] --> draft
    draft --> validating
    validating --> deployed
    validating --> failed
    deployed --> invoking
    invoking --> succeeded
    invoking --> retrying
    retrying --> succeeded
    retrying --> failed
    deployed --> archived
```

## Additional State Machines

```mermaid
stateDiagram-v2
    [*] --> draft
    draft --> validating
    validating --> active
    active --> switching
    switching --> verifying
    verifying --> active
    switching --> rollback
    rollback --> active
    switching --> failed
    failed --> [*]
```

- Invalid transition attempts return `STATE_INVALID_TRANSITION`.
- Transition guards include contract compatibility checks and SLO burn-rate gates.
