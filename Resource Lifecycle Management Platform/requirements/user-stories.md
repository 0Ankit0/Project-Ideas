# User Stories — Resource Lifecycle Management Platform

## Personas

| Persona | Role | Primary Goal |
|---------|------|-------------|
| **Requestor** | Customer / end user who borrows resources | Reserve and use resources with minimal friction |
| **Resource Manager** | Operator managing the catalog and day-to-day operations | Maintain accurate inventory and prevent conflicts |
| **Custodian** | Field staff who hand over and receive resources physically | Complete checkouts/check-ins quickly and accurately |
| **Operations Admin** | Back-office administrator for configuration | Configure policies, SLAs, and resource types |
| **Finance Manager** | Manages deposits, charges, and settlement | Ensure accurate, timely settlement of all transactions |
| **Compliance Officer** | Audits activity for policy and regulatory adherence | Access audit trails and incident reports |

---

## User Stories

### Requestor Stories

---

#### US-01 — Reserve a Resource

> **As a** Requestor,  
> **I want to** search for available resources by type, date range, and location and create a reservation,  
> **so that** I can guarantee access to the resource I need.

**Acceptance Criteria:**
- [ ] Availability calendar shows open slots in real time
- [ ] System rejects reservation if requested slot overlaps an existing confirmed booking (BR-01)
- [ ] System enforces minimum lead time (30 min standard / 24 h premium) (BR-02)
- [ ] Confirmation email/SMS sent within 60 seconds of successful reservation
- [ ] Reservation enters PENDING state; customer can view it in the portal
- [ ] Reservation auto-expires after 15 min if not confirmed by an operator

**MoSCoW Priority:** Must  
**Story Points:** 5

---

#### US-02 — Cancel a Reservation

> **As a** Requestor,  
> **I want to** cancel my reservation before the lead-time cutoff,  
> **so that** I am not charged a cancellation fee when I no longer need the resource.

**Acceptance Criteria:**
- [ ] Customer can cancel from their portal up to the lead-time cutoff
- [ ] Cancellations within the cutoff window generate a configurable cancellation fee charge
- [ ] Cancelled reservation releases the availability window immediately
- [ ] Cancellation confirmation sent via email and SMS
- [ ] If a deposit hold was already placed, it is released within 24 hours

**MoSCoW Priority:** Must  
**Story Points:** 3

---

#### US-03 — Complete Checkout

> **As a** Requestor,  
> **I want to** complete checkout at the resource location by scanning the barcode,  
> **so that** I can begin using the resource immediately with my checkout confirmed.

**Acceptance Criteria:**
- [ ] Barcode scan identifies correct ResourceUnit
- [ ] System validates active allocation exists for customer
- [ ] System initiates deposit hold against stored payment method (BR-03)
- [ ] Checkout blocked if deposit hold fails
- [ ] CheckoutRecord created with pre-condition notes and optional photos
- [ ] Resource state transitions to CHECKED_OUT

**MoSCoW Priority:** Must  
**Story Points:** 8

---

#### US-04 — View Reservation and Checkout History

> **As a** Requestor,  
> **I want to** view my past and current reservations and checkouts in a self-service portal,  
> **so that** I can track usage history and pending deposit returns.

**Acceptance Criteria:**
- [ ] Portal lists all reservations with status, dates, and resource name
- [ ] Each checkout shows deposit status (held / released / partially retained)
- [ ] Settlement breakdown is accessible from completed checkouts
- [ ] Export to PDF or CSV available for the last 12 months

**MoSCoW Priority:** Should  
**Story Points:** 3

---

### Resource Manager Stories

---

#### US-05 — Catalog a New Resource

> **As a** Resource Manager,  
> **I want to** add a new resource unit to the catalog with barcode, location, and attributes,  
> **so that** it becomes immediately available for reservation by customers.

**Acceptance Criteria:**
- [ ] Form validates required fields: serial number, type, location, barcode
- [ ] System publishes `ResourceCataloged` event on save
- [ ] Resource starts in DRAFT state; must be explicitly activated
- [ ] Activation publishes `ResourceActivated` event and makes unit visible in availability calendar
- [ ] Duplicate barcode rejected with clear error message

**MoSCoW Priority:** Must  
**Story Points:** 5

---

#### US-06 — Assign Custodian to Checkout

> **As a** Resource Manager,  
> **I want to** assign a specific custodian to handle a checkout for an allocation,  
> **so that** the custodian can verify identity and capture condition at handoff.

**Acceptance Criteria:**
- [ ] Manager can select custodian from staff directory
- [ ] Custodian receives push notification with checkout details
- [ ] System records manager identity as allocating_operator on AllocationRecord

**MoSCoW Priority:** Should  
**Story Points:** 2

---

#### US-07 — Schedule Preventive Maintenance

> **As a** Resource Manager,  
> **I want to** schedule a preventive maintenance window for a resource,  
> **so that** it is taken offline safely without conflicting with existing reservations.

**Acceptance Criteria:**
- [ ] Manager selects resource, maintenance type, start/end time, and technician
- [ ] System checks for conflicting reservations before scheduling
- [ ] Conflicting reservations are auto-cancelled with notification (BR-05)
- [ ] Resource state transitions to MAINTENANCE; new reservations blocked (BR-05)
- [ ] `MaintenanceScheduled` event published
- [ ] On maintenance completion, resource returns to ACTIVE / AVAILABLE

**MoSCoW Priority:** Must  
**Story Points:** 5

---

### Custodian Stories

---

#### US-08 — File Condition Report at Check-In

> **As a** Custodian,  
> **I want to** file a condition report when a customer returns a resource,  
> **so that** any damage is documented immediately with photographic evidence.

**Acceptance Criteria:**
- [ ] Custodian can scan barcode to identify return
- [ ] Form accepts damage severity (NONE / MINOR / MODERATE / SEVERE), description, up to 10 photos
- [ ] Report must be filed within 2 h of check-in; missing report triggers auto P2 incident (BR-04)
- [ ] If severity ≥ MODERATE, system auto-creates Incident and places deposit hold (BR-06)
- [ ] `ConditionReportFiled` event published

**MoSCoW Priority:** Must  
**Story Points:** 8

---

#### US-09 — Handle Offline Barcode Scan

> **As a** Custodian,  
> **I want to** complete a checkout or check-in even when the barcode scanner is offline,  
> **so that** operations are not blocked by network or device failures.

**Acceptance Criteria:**
- [ ] Mobile app allows manual barcode entry as fallback
- [ ] Offline transactions are queued locally and synced when connectivity is restored
- [ ] Conflict detection is performed on sync, with duplicate rejection
- [ ] Audit log marks offline-originated records with `source: offline`

**MoSCoW Priority:** Should  
**Story Points:** 5

---

### Operations Admin Stories

---

#### US-10 — Configure SLA Profile

> **As an** Operations Admin,  
> **I want to** define an SLA profile for a premium resource type with a 99.5% monthly availability guarantee,  
> **so that** breaches are detected automatically and credits are issued without manual intervention.

**Acceptance Criteria:**
- [ ] Admin can set: availability_target_pct, measurement_window, breach_threshold_minutes, credit_value
- [ ] System monitors resource availability against the SLA window in real time
- [ ] On breach: `SLABreachDetected` event published; credit issued to customer account automatically (BR-09)
- [ ] Breach history is queryable via the compliance report

**MoSCoW Priority:** Must  
**Story Points:** 5

---

#### US-11 — Define Resource Policy

> **As an** Operations Admin,  
> **I want to** configure a policy for a resource type specifying deposit amount, late-fee rate, and damage rate card,  
> **so that** financial calculations are consistent and auditable.

**Acceptance Criteria:**
- [ ] Policy fields: deposit_amount, lead_time_minutes, late_fee_per_hour, damage_rate_card (JSON), cancellation_fee_pct
- [ ] Policies are versioned; active version used at checkout time; version recorded on CheckoutRecord
- [ ] System rejects deposit holds with amount less than policy.deposit_amount (BR-03)

**MoSCoW Priority:** Must  
**Story Points:** 3

---

### Finance Manager Stories

---

#### US-12 — Approve Settlement

> **As a** Finance Manager,  
> **I want to** review and approve damage settlements before funds are disbursed,  
> **so that** all financial adjustments are authorised and auditable.

**Acceptance Criteria:**
- [ ] Settlement dashboard shows: incident details, assessed damage charge, late fees, deposit held, proposed refund
- [ ] Manager can approve, reject, or modify the assessed damage charge with justification note
- [ ] On approval: deposit capture or release executed via payment gateway
- [ ] `ChargeSettled` and `DepositReleased` events published
- [ ] Settlement posted to ERP ledger within 5 minutes of approval

**MoSCoW Priority:** Must  
**Story Points:** 8

---

#### US-13 — Generate Settlement Report

> **As a** Finance Manager,  
> **I want to** generate a monthly settlement reconciliation report,  
> **so that** I can verify all deposits and charges balance against payment gateway records.

**Acceptance Criteria:**
- [ ] Report covers a selectable date range
- [ ] Includes: total deposits held, total charges captured, total refunds, outstanding unsettled incidents
- [ ] Exportable as CSV and PDF
- [ ] Reconciliation discrepancies are flagged with case reference

**MoSCoW Priority:** Should  
**Story Points:** 3

---

### Compliance Officer Stories

---

#### US-14 — Audit Resource Lifecycle Events

> **As a** Compliance Officer,  
> **I want to** query the full event history for any resource unit,  
> **so that** I can produce a chain-of-custody report for audits or legal proceedings.

**Acceptance Criteria:**
- [ ] Event log is immutable and includes: event type, timestamp, actor, before/after state snapshot
- [ ] Searchable by resource ID, customer ID, date range, event type
- [ ] Export to signed PDF for legal submission
- [ ] Audit log access is itself logged (access audit trail)

**MoSCoW Priority:** Must  
**Story Points:** 5

---

#### US-15 — Review Incident Reports

> **As a** Compliance Officer,  
> **I want to** review all open incidents with their escalation status and evidence,  
> **so that** I can ensure policy-compliant resolution within defined SLAs.

**Acceptance Criteria:**
- [ ] Incident list filterable by: type, severity, status, escalation level, customer
- [ ] Each incident shows: timeline, escalation history, linked condition report and photos
- [ ] Overdue escalation (24 h) incidents flagged with legal-hold status
- [ ] Resolution notes and settlement outcome visible when closed

**MoSCoW Priority:** Must  
**Story Points:** 3

---

#### US-16 — Monitor Overdue Escalations

> **As a** Compliance Officer,  
> **I want to** receive a daily digest of resources still overdue after the 24-hour escalation threshold,  
> **so that** legal action can be initiated promptly when required.

**Acceptance Criteria:**
- [ ] Daily 08:00 digest email listing all resources in LEGAL_HOLD state
- [ ] Digest includes customer contact info, resource value, duration overdue
- [ ] Officer can trigger manual escalation from within the digest portal link

**MoSCoW Priority:** Should  
**Story Points:** 2
