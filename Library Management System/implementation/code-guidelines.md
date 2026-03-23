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
