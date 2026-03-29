# Code Guidelines - Library Management System

## Reference Implementation Stack
- Frontend: React + TypeScript for patron portal and staff workspace
- Backend: TypeScript service layer (for example NestJS) with modular domain packages
- Persistence: PostgreSQL for transactional data, search index for discovery, object storage for imports/exports
- Async processing: queue + workers for notifications, overdue jobs, search projection, and batch imports

## Suggested Repository Structure

```text
library-platform/
├── apps/
│   ├── patron-portal/
│   ├── staff-workspace/
│   ├── api/
│   └── worker/
├── packages/
│   ├── domain/
│   │   ├── catalog/
│   │   ├── patrons/
│   │   ├── circulation/
│   │   ├── holds/
│   │   ├── acquisitions/
│   │   └── policies/
│   ├── ui/
│   └── shared/
├── infra/
└── tests/
```

## Domain Boundaries
- Keep catalog, circulation, holds, fines, acquisitions, and policy logic in separate modules.
- Use domain events for notifications, search indexing, reporting, and digital-provider sync rather than direct write-path coupling.
- Avoid exposing staff-only policy or patron-history fields to patron-facing APIs.

## Backend Guidelines
- Treat barcode and RFID identifiers as externally visible business keys, but preserve internal UUIDs for system joins.
- Keep due-date and fine calculations inside policy services rather than controllers or UI layers.
- Maintain append-only financial and audit histories for waivers, write-offs, and adjustments.
- Separate title-level records from copy/item-level records everywhere in the model.

## Frontend Guidelines
- Optimize the patron portal for search, account visibility, and hold management.
- Optimize the staff workspace for fast scan-driven flows and exception handling.
- Keep queue, transfer, and inventory views highly filterable for operational users.

## Example Domain Types

```ts
export type ItemCopyStatus =
  | 'cataloging'
  | 'available'
  | 'on_loan'
  | 'overdue'
  | 'on_hold_shelf'
  | 'in_transfer'
  | 'in_repair'
  | 'lost'
  | 'withdrawn';

export interface CreateLoanCommand {
  patronId: string;
  itemBarcode: string;
  issuedAtBranchId: string;
  operatorId: string;
}
```

## Testing Expectations
- Unit tests for policy evaluation, queue advancement, and fine calculations.
- Integration tests for checkout, return, renew, hold fulfillment, and branch transfer workflows.
- API contract tests for patron-facing and staff-facing endpoints.
- E2E tests for search-to-hold, checkout-to-return, acquisition-to-catalog, and inventory-audit flows.

## Borrowing & Reservation Lifecycle, Consistency, Penalties, and Exception Patterns

### Artifact focus: Implementation conventions for circulation

This section is intentionally tailored for this specific document so implementation teams can convert architecture and analysis into build-ready tasks.

### Implementation directives for this artifact
- Standardize command handler template: validate -> lock/load -> mutate -> persist -> outbox -> emit response.
- Require deterministic clock abstraction for testable due-date and fine calculations.
- Enforce structured logging with correlation and policy decision fields.

### Lifecycle controls that must be reflected here
- Borrowing must always enforce policy pre-checks, deterministic copy selection, and atomic loan/copy updates.
- Reservation behavior must define queue ordering, allocation eligibility re-checks, and pickup expiry/no-show outcomes.
- Fine and penalty flows must define accrual formula, cap behavior, and lost/damage adjudication paths.
- Exception handling must define idempotency, conflict semantics, outbox reliability, and operator recovery procedures.

### Traceability requirements
- Every major rule in this document should map to at least one API contract, domain event, or database constraint.
- Include policy decision codes and audit expectations wherever staff override or monetary adjustment is possible.

### Definition of done for this artifact
- Content is specific to this artifact type and not a generic duplicate.
- Rules are testable (unit/integration/contract) and reference concrete data/events/errors.
- Diagram semantics (if present) are consistent with textual constraints and lifecycle behavior.
