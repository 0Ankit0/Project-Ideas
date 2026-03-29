# State Machine Diagram - Restaurant Management System

## Order Lifecycle

```mermaid
stateDiagram-v2
    [*] --> draft
    draft --> submitted
    submitted --> in_preparation
    in_preparation --> ready
    ready --> served
    served --> billed
    billed --> settled
    draft --> voided
    submitted --> voided
    in_preparation --> delayed
    delayed --> in_preparation
    ready --> refire
    refire --> in_preparation
```

## Table Lifecycle

```mermaid
stateDiagram-v2
    [*] --> available
    available --> reserved
    available --> occupied
    reserved --> occupied
    occupied --> bill_pending
    bill_pending --> cleaning
    cleaning --> available
    occupied --> merged
    merged --> occupied
    reserved --> no_show
    no_show --> available
```

## Cancellation and Reversal State Machine

```mermaid
stateDiagram-v2
    [*] --> requested
    requested --> policy_evaluation
    policy_evaluation --> pending_approval: approval_required
    policy_evaluation --> approved: auto_approved
    pending_approval --> approved: manager_or_dual_approval
    pending_approval --> rejected: denied
    approved --> compensation_executing
    compensation_executing --> completed: all_compensations_success
    compensation_executing --> partial_failure: one_or_more_fail
    partial_failure --> compensation_executing: retry
    completed --> [*]
    rejected --> [*]
```

## Peak-Load Control State Machine

```mermaid
stateDiagram-v2
    [*] --> normal
    normal --> watch: warn_threshold_crossed
    watch --> surge: surge_threshold_crossed
    surge --> critical: critical_threshold_crossed
    critical --> emergency_controls: persistent_breach
    emergency_controls --> critical: partial_relief
    critical --> surge: metrics_recover
    surge --> watch: stable_window
    watch --> normal: sustained_stability
```

## Transition Rules (Must Enforce)
- `submitted -> voided` allowed only before station acceptance unless manager override.
- `paid -> refunded` requires linked refund intent and approval policy evaluation.
- `occupied -> cleaning` requires terminal check state (`paid`, `voided`, or approved house-account hold).
- `surge/critical -> normal` transitions require sustained recovery window and no unresolved critical alerts.
