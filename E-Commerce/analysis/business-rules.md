# Business Rules

These rules govern policy enforcement and exception handling for E-Commerce.

## Lifecycle and State Rules
1. State transitions must follow approved workflow paths and be validated server-side.
2. Any terminal-state reversal requires elevated authorization and an auditable reason code.
3. Conflicting operations on the same active record must use optimistic locking or queue serialization.

## Financial and Compliance Rules
1. Amount calculations must be deterministic and reproducible from source inputs.
2. Policy-sensitive actions (refunds, overrides, waivers, manual adjustments) require dual logging: business event + audit event.
3. PII-relevant operations must enforce least-privilege access and export redaction controls.

## Operational Rules
1. Every failed asynchronous integration must emit retry metadata and escalation thresholds.
2. Critical workflow deadlines must generate alerts before SLA breach windows.
3. Manual interventions must attach operator notes and remediation outcomes.
