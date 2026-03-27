# Swimlane Diagrams

## Lanes
- **Customer Lane:** discovery, reservation actions, cancellation requests.
- **Operations Lane:** fulfillment, return processing, evidence capture.
- **Finance Lane:** charge computation, reconciliation, exceptions.
- **Platform Lane:** policy checks, orchestration, audit event emission.

## Handoffs
- Customer -> Platform on reservation command.
- Platform -> Operations on fulfillment readiness.
- Operations -> Finance on return/incident outcomes.
