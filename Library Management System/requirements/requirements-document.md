# Requirements Document - Library Management System

## 1. Project Overview

### 1.1 Purpose
Build a comprehensive library management platform for a multi-branch public or institutional library that supports patron services, circulation, cataloging, acquisitions, branch operations, compliance, and optional digital lending in a single system.

### 1.2 Scope

| In Scope | Out of Scope |
|----------|--------------|
| Physical catalog and copy/item tracking | Full university ERP or SIS replacement |
| Patron account lifecycle and membership rules | Original content creation or publishing workflows |
| Search, issue, return, renew, hold, and waitlist flows | General retail commerce platform |
| Fines, waivers, fee events, and payment reconciliation hooks | Full accounting ledger replacement |
| Acquisitions, receiving, accession, and inventory audits | Large-scale archival preservation systems |
| Multi-branch operations and transfers | Advanced research repository management |
| Optional digital lending and license controls | Broad learning management workflows |

### 1.3 Operating Model
- The system assumes multiple branches share a central catalog while holding branch-specific copies/items.
- Patrons may borrow across branches according to policy and can optionally access licensed digital materials.
- Staff access is segmented by role, branch scope, and operational privileges.

### 1.4 Primary Actors

| Actor | Goals |
|-------|-------|
| Patron | Discover materials, borrow or reserve them, manage account status, and receive updates |
| Librarian / Circulation Staff | Serve patrons, execute circulation, manage queues, and resolve exceptions |
| Cataloging Staff | Maintain data quality, classifications, authority records, and deduplication |
| Acquisitions Staff | Procure resources, manage vendors, receive materials, and track budgets or stock intake |
| Branch Manager | Monitor circulation, inventory, transfer health, and branch-level compliance |
| Admin | Define policies, roles, integrations, retention, and system configuration |

## 2. Functional Requirements

### 2.1 Identity, Membership, and Access Control

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-IAM-001 | System shall support patron, staff, and administrator accounts with role-based access control | Must Have |
| FR-IAM-002 | System shall maintain membership status, expiry, borrowing eligibility, and branch affiliation for patrons | Must Have |
| FR-IAM-003 | System shall support branch-scoped staff permissions and centrally managed admin roles | Must Have |
| FR-IAM-004 | System shall audit privileged actions, policy changes, waivers, and inventory adjustments | Must Have |

### 2.2 Catalog and Discovery

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-CAT-001 | System shall manage bibliographic records for books and other media with ISBN/identifier support where applicable | Must Have |
| FR-CAT-002 | System shall support multiple copies/items per title with branch-specific status, barcode/RFID, and shelf location | Must Have |
| FR-CAT-003 | System shall provide search and filtering by title, author, subject, identifier, format, language, availability, and branch | Must Have |
| FR-CAT-004 | System shall support subject tagging, classification metadata, and duplicate-record merge workflows | Must Have |
| FR-CAT-005 | System shall expose availability and hold-queue information to patrons and staff in near real time | Must Have |

### 2.3 Circulation and Patron Services

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-CIR-001 | Staff shall issue items to eligible patrons using barcode/RFID or account lookup | Must Have |
| FR-CIR-002 | System shall support returns, renewals, due-date calculation, and overdue tracking | Must Have |
| FR-CIR-003 | System shall support exception states for lost, damaged, missing, claimed-returned, and in-repair items | Must Have |
| FR-CIR-004 | System shall enforce policy-based borrowing limits by patron type, item type, and branch rules | Must Have |
| FR-CIR-005 | System shall maintain complete circulation history and patron-facing account views | Must Have |

### 2.4 Reservations, Holds, and Notifications

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-HLD-001 | Patrons and staff shall place holds on eligible titles or specific items according to policy | Must Have |
| FR-HLD-002 | System shall manage hold queues with pickup branch, expiration, and priority rules | Must Have |
| FR-HLD-003 | System shall notify patrons when holds are available, expiring, overdue, or blocked by account restrictions | Must Have |
| FR-HLD-004 | System shall support waitlist transitions during return, transfer, or cancellation events | Must Have |

### 2.5 Fines, Fees, and Financial Events

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-FIN-001 | System shall calculate overdue fines and replacement charges according to configurable policies | Must Have |
| FR-FIN-002 | Staff shall be able to record payments, waivers, adjustments, and dispute notes with audit history | Must Have |
| FR-FIN-003 | System shall block borrowing when account thresholds or policy restrictions are exceeded | Must Have |
| FR-FIN-004 | System shall provide exportable financial-event reports for reconciliation | Should Have |

### 2.6 Acquisitions, Inventory, and Branch Operations

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-INV-001 | Staff shall create purchase requests, purchase orders, receiving records, and accession entries | Must Have |
| FR-INV-002 | System shall support vendor records, expected delivery tracking, and receiving discrepancies | Must Have |
| FR-INV-003 | Branches shall execute transfers, shelf audits, and stock counts with discrepancy logging | Must Have |
| FR-INV-004 | System shall support write-off and repair workflows for lost or damaged materials | Must Have |
| FR-INV-005 | Branch managers shall monitor utilization, stock gaps, and transfer turnaround metrics | Should Have |

### 2.7 Digital Lending and Resource Access

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-DIG-001 | System shall optionally integrate with digital content providers for e-books or audiobooks | Should Have |
| FR-DIG-002 | System shall enforce license counts, access windows, and concurrent-use limits | Should Have |
| FR-DIG-003 | Patrons shall see digital entitlements and loan expirations in their account view | Should Have |

### 2.8 Reporting, Administration, and Operations

| ID | Requirement | Priority |
|----|-------------|----------|
| FR-OPS-001 | System shall provide dashboards for circulation volume, overdue counts, hold queues, inventory exceptions, and branch performance | Must Have |
| FR-OPS-002 | Administrators shall configure circulation policies, holidays, branch calendars, patron categories, and notification templates | Must Have |
| FR-OPS-003 | System shall support exportable audit trails, inventory reports, and patron-service summaries | Must Have |
| FR-OPS-004 | System shall provide event logs and operational observability for integrations and background jobs | Must Have |

## 3. Non-Functional Requirements

| ID | Requirement | Target |
|----|-------------|--------|
| NFR-P-001 | Search response time | < 500 ms p95 |
| NFR-P-002 | Checkout or return transaction completion | < 2 seconds p95 |
| NFR-P-003 | Availability update propagation | < 60 seconds |
| NFR-A-001 | Service availability | 99.9% monthly |
| NFR-S-001 | Concurrent active users | 10,000+ |
| NFR-S-002 | Supported catalog size | 5M+ bibliographic records |
| NFR-SEC-001 | Encryption | TLS 1.3 in transit, AES-256 at rest |
| NFR-SEC-002 | Audit coverage | 100% privileged actions logged |
| NFR-PRV-001 | Patron privacy | No unauthorized disclosure of reading history |
| NFR-UX-001 | Accessibility | WCAG 2.1 AA for key patron and staff workflows |

## 4. Constraints and Assumptions

- The implementation must support a shared catalog with branch-specific inventory.
- Barcode support is assumed; RFID integration should remain optional.
- Digital lending is optional but should be structurally supported in the design.
- Financial handling may integrate with external payment systems rather than becoming a full accounting system.
- Policy engines must remain configurable because borrowing rules differ across branches and patron categories.

## 5. Success Metrics

- 95% of standard issue and return transactions complete without manual override.
- 100% of cataloged items remain traceable by branch, status, and last transaction.
- 100% of fine waivers and inventory write-offs are auditable.
- Hold queue movement is visible and correct for all returned or canceled items.
- Branch managers can identify overdue risk, missing stock, and transfer bottlenecks from one dashboard.

## Borrowing & Reservation Lifecycle, Consistency, Penalties, and Exception Patterns

### 1) Implementation-Ready Domain Lifecycle

#### 1.1 Borrowing lifecycle with hard gates
| Stage | Command | Required checks (fail-fast) | Atomic writes | Events |
|---|---|---|---|---|
| Discover | `SearchCatalog` | Tenant scope, branch visibility, suppressed record filtering | none | `SearchExecuted` (optional analytics) |
| Loan intent | `BeginCheckout` | Account active, max-loans, unpaid balance threshold, item circulation policy, embargo/recall | checkout session token | `CheckoutStarted` |
| Commit checkout | `CommitCheckout` | copy version unchanged, hold ownership valid, no active conflicting loan | loan row, copy state `OnLoan`, due-policy snapshot, ledger seed | `LoanCreated`, `CopyStateChanged` |
| Mid-loan | `RenewLoan` | renewal limit, hold queue empty or borrower is next hold owner, not recalled | due date revision + policy snapshot delta | `LoanRenewed` |
| Return | `ReturnCopy` | active loan exists and matches copy barcode | loan close, copy state transition, fine recompute, condition assessment | `LoanClosed`, `FineAssessed?`, `CopyStateChanged` |
| Fulfillment | `AllocateHold` | queue non-empty, requester still eligible, pickup branch open-window | hold allocation + pickup expiry + shelf location | `HoldAllocated`, `PickupDeadlineAssigned` |

#### 1.2 Reservation lifecycle (title-level and copy-level)
1. **Place hold** (`PlaceHold`): validate duplicate hold policy + patron eligibility + branch delivery constraints.
2. **Queue rank**: deterministic ordering uses `(priority_lane, created_at, hold_id)` to avoid tie ambiguity.
3. **Eligibility re-check**: at allocation time, rerun account/fine limits and suspension rules.
4. **Pickup phase**: move to `AwaitingPickup`, set `pickup_by`, send notice batch with retry/backoff.
5. **Expiry/no-show**: on expiry, apply no-show strike policy, release copy, trigger next allocation.
6. **Idempotent cancel**: repeated cancel requests return success without duplicate side effects.

### 2) Inventory Consistency Constraints (source-of-truth rules)

#### 2.1 Relational invariants (must be enforceable in DB + service)
- **Exclusive copy state**: each copy has exactly one lifecycle state at any instant.
- **Loan-to-copy cardinality**: `copy.state='OnLoan'` iff exactly one open `loan` exists.
- **Hold allocation uniqueness**: one copy can back only one active pickup allocation.
- **Transfer conservation**: `InTransit` decrement at source must equal increment at destination upon receipt.
- **Soft-delete safety**: withdrawn/lost copies cannot be allocated, renewed, or transferred.

#### 2.2 Suggested persistence constraints
- Unique partial index for open loans: `(copy_id) WHERE closed_at IS NULL`.
- Unique partial index for active hold allocation: `(copy_id) WHERE allocation_status IN ('Allocated','AwaitingPickup')`.
- Check constraint for due dates: `due_at > checked_out_at`.
- Foreign-key + `ON UPDATE RESTRICT` for policy snapshots to preserve historical billing logic.

#### 2.3 Concurrency control
- Use optimistic locking (`row_version`) on `copy`, `loan`, and `hold`.
- Treat version mismatch as retryable conflict (`409 COPY_STATE_CHANGED`).
- Wrap checkout/return/allocation in SERIALIZABLE or explicit `SELECT ... FOR UPDATE` critical sections.

### 3) Fine/Fee/Penalty Computation Rules

#### 3.1 Fine engine contract
```text
fine = min(policy.max_cap,
           max(0, overdue_units - grace_units) * unit_rate)
```
- `overdue_units` must be timezone-aware and calendar-policy aware.
- Closed-day carry rules must be policy-configurable (pause accrual vs continue accrual).
- Fine policy snapshot is immutable per-loan to avoid retroactive disputes.

#### 3.2 Lost/damaged material handling
- **Presumed lost** after `lost_after_days` threshold: post replacement + processing fees.
- **Found after billed**: automatically generate reversing credits according to refund window policy.
- **Damage tiers** (`Minor`, `Moderate`, `Severe`, `Unusable`) map to fixed or bounded fee ranges.

#### 3.3 Patron sanctions
- Restrict checkout when `outstanding_balance >= borrow_block_threshold`.
- Restrict renewals when item is recalled or hold queue length > 0.
- Apply temporary suspension for repeated no-show pickups, waived only with authorized override.

### 4) Exception Handling and Reliability Patterns

#### 4.1 Error taxonomy (machine-readable)
| Code | HTTP | Retry | Meaning |
|---|---:|---|---|
| `COPY_STATE_CHANGED` | 409 | Yes | Copy version changed during command processing |
| `HOLD_NOT_ELIGIBLE` | 422 | No | Patron no longer satisfies hold policy |
| `BORROWING_BLOCKED_BALANCE` | 403 | No | Patron balance exceeds threshold |
| `OUTBOX_PUBLISH_TIMEOUT` | 503 | Yes | Domain write succeeded; event publish pending retry |
| `PAYMENT_PROVIDER_UNAVAILABLE` | 503 | Yes | Fee payment failed due to external outage |

#### 4.2 Transaction + outbox pattern
1. Commit domain state and outbox record in one transaction.
2. Background publisher delivers outbox events with at-least-once guarantees.
3. Consumers enforce idempotency using `event_id` dedupe store.
4. Dead-letter queue receives poison messages after retry budget exhaustion.

#### 4.3 Compensations
- If notification fails after successful allocation, keep allocation state and retry notice (no rollback).
- If payment capture fails during replacement fee flow, mark fee as `PendingPayment` and keep sanctions active.
- Manual overrides require privileged role + mandatory reason code + immutable audit entry.

### 5) API/Workflow Contract Details (implementation checklist)
- Every mutating endpoint must accept `Idempotency-Key` and return prior result on replay.
- Response payloads must include `policy_decision_code` and `policy_snapshot_id` for support traceability.
- Commands must emit correlation IDs propagated to logs, metrics, and event envelopes.
- Retryable errors must include `retry_after_ms` guidance when backoff is appropriate.
- Pagination for holds/loans must be cursor-based (stable ordering by `created_at, id`).

### 6) Operational Readiness Requirements
- **SLOs**: checkout p95 < 300ms, return p95 < 350ms, hold allocation lag < 60s.
- **Reconciliation jobs**: hourly invariant scan for copy-state/loan mismatch and hold-allocation drift.
- **Audit coverage**: all policy overrides, fee waivers, and force-state actions must be tamper-evident.
- **Observability**: metrics for conflict rates, failed compensations, DLQ depth, and fine disputes.
- **Runbooks**: include procedures for replaying outbox events, clearing DLQ, and reversing mistaken fees.

### 7) Security, Compliance, and Privacy Controls
- Enforce least-privilege RBAC for circulation actions and financial adjustments.
- Encrypt patron PII at rest and in transit; tokenize payment references.
- Retain audit events per regulatory schedule; redact PII from long-term analytics streams.
- Record consent and legal basis for notification channels (email/SMS/push).

### 8) Mermaid Lifecycle Reference (for implementers)
```mermaid
stateDiagram-v2
    [*] --> Available
    Available --> OnLoan: CommitCheckout
    OnLoan --> OnLoan: RenewLoan
    OnLoan --> OnHoldShelf: ReturnCopy + HoldAllocated
    OnLoan --> Available: ReturnCopy + NoActiveHold
    OnLoan --> Lost: LostThresholdExceeded
    OnHoldShelf --> OnLoan: PickupCheckout
    OnHoldShelf --> Available: PickupExpired
    Available --> InTransit: TransferDispatch
    InTransit --> Available: TransferReceive
    Available --> Repair: DamageIntake
    Repair --> Available: RepairCompleted
    Lost --> Available: FoundAndReinstated
```

### 9) Definition of Done for this documentation area
- Lifecycle states, commands, and transitions are unambiguous and testable.
- Invariants are enforceable in both DB schema and service logic.
- Penalty calculations are deterministic with snapshot-based traceability.
- Failure modes map to explicit error codes, retry semantics, and operator runbooks.
- Mermaid diagrams and textual rules are consistent with each other and with API contracts.

