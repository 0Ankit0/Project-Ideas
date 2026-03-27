# Use Case Diagram

## Primary Actors
- Consumer / Requestor
- Provider / Operator
- Fulfillment Agent
- Finance Analyst
- Compliance Auditor

## Core Use Cases
1. Manage Resource Catalog
2. Manage Availability & Holds
3. Create/Amend/Cancel Reservation
4. Fulfill (Check-out/Activation)
5. Return & Inspect
6. Finalize Settlement
7. Manage Incident / Dispute
8. Audit Lifecycle History

## Relationship Notes
- Reservation and fulfillment use cases include `<<include>> Policy Evaluation`.
- Settlement includes `<<extend>> Dispute Review` when incident thresholds are met.
