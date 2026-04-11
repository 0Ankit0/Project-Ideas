# Edge Cases: Deployment Failures

## Traceability
- Requirements: [`../requirements/requirements.md`](../requirements/requirements.md)
- Deployment design: [`../detailed-design/sequence-diagrams.md`](../detailed-design/sequence-diagrams.md)
- Execution controls: [`../implementation/implementation-guidelines.md`](../implementation/implementation-guidelines.md)

## Scenario Set: Deployment Rollback Failure

### Trigger
Rollback starts after canary regression, but previous revision cannot start due to missing config/secret mismatch.

```mermaid
sequenceDiagram
  participant CD as CD Controller
  participant RT as Runtime
  participant SEC as Secret Manager
  participant OPS as On-call

  CD->>RT: Initiate rollback to rev N-1
  RT->>SEC: Fetch secret version for rev N-1
  SEC-->>RT: Secret missing/invalid
  RT-->>CD: Rollback failed
  CD->>OPS: Page incident + freeze deploys
  OPS->>SEC: Restore previous secret version
  OPS->>RT: Retry rollback
  RT-->>CD: Rollback successful
```

### Invariants
- Rollback candidate must include immutable config+secret version references.
- Rollback cannot proceed if safety checks detect incompatible schema state.

### Operational acceptance criteria
- Failed rollback automatically freezes subsequent deployments for impacted app.
- Incident timeline captures revision IDs, secret versions, and operator actions.
- Runbook exercise proves recovery in < 15 minutes.

---

**Status**: Complete  
**Document Version**: 2.0
